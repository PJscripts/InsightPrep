import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

function Interview() {
  const { sessionId } = useParams();
  const navigate = useNavigate();

  const audioRef = useRef(null);
  const audioUrlRef = useRef("");
  const recognitionRef = useRef(null);
  const finalTranscriptRef = useRef("");
  const baseAnswerRef = useRef("");
  const listeningRequestedRef = useRef(false);
  const stoppingRef = useRef(false);

  const [question, setQuestion] = useState(null);
  const [answer, setAnswer] = useState("");
  const [interimTranscript, setInterimTranscript] = useState("");
  const [answerMode, setAnswerMode] = useState("type");
  const [listening, setListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(true);
  const [audioReady, setAudioReady] = useState(false);
  const [audioError, setAudioError] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const Recognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      setSpeechSupported(false);
    }

    return () => {
      listeningRequestedRef.current = false;
      stoppingRef.current = true;

      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {
          // Ignore cleanup failures.
        }
        recognitionRef.current = null;
      }

      revokeAudio();
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function fetchQuestion() {
      try {
        const response = await fetch(
          `http://localhost:8000/interviews/sessions/${sessionId}/current`,
          { credentials: "include" },
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || "Failed to load question.");
        }

        if (!cancelled) {
          stopListening();
          setQuestion(data);
          setError("");
          setAnswer("");
          setInterimTranscript("");
          finalTranscriptRef.current = "";
          baseAnswerRef.current = "";
          setAnswerMode("type");
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchQuestion();

    return () => {
      cancelled = true;
      stopListening();
      revokeAudio();
    };
  }, [sessionId]);

  useEffect(() => {
    if (!question?.question_text) return;

    let cancelled = false;

    async function loadQuestionAudio() {
      setAudioReady(false);
      setAudioError("");
      revokeAudio();

      try {
        const response = await fetch(
          `http://localhost:8000/interviews/sessions/${sessionId}/question/audio`,
          { credentials: "include" },
        );

        if (!response.ok) {
          const body = await response.json().catch(() => ({}));
          throw new Error(
            body.detail || "Question audio is unavailable.",
          );
        }

        const blob = await response.blob();

        if (cancelled) return;

        const url = URL.createObjectURL(blob);
        audioUrlRef.current = url;

        if (audioRef.current) {
          audioRef.current.src = url;
          audioRef.current.load();
        }

        setAudioReady(true);

        try {
          await audioRef.current?.play();
        } catch {
          // Browser autoplay may be blocked; the replay button remains available.
        }
      } catch (err) {
        if (!cancelled) {
          setAudioError(err.message);
        }
      }
    }

    loadQuestionAudio();

    return () => {
      cancelled = true;
      revokeAudio();
    };
  }, [question?.question_number, question?.question_text, sessionId]);

  function revokeAudio() {
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = "";
    }
  }

  function getSpeechLanguage() {
    const browserLanguage =
      navigator.language || navigator.userLanguage || "en-US";

    return browserLanguage.toLowerCase().startsWith("en-in")
      ? "en-IN"
      : "en-US";
  }

  function startListening() {
    const Recognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!Recognition) {
      setSpeechSupported(false);
      return;
    }

    if (listeningRequestedRef.current) return;

    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch {
        // Ignore stale recognizer cleanup.
      }
      recognitionRef.current = null;
    }

    const existingAnswer = answer.trim();
    baseAnswerRef.current = existingAnswer;
    finalTranscriptRef.current = "";
    listeningRequestedRef.current = true;
    stoppingRef.current = false;
    setInterimTranscript("");
    setError("");

    function createRecognition() {
      const recognition = new Recognition();

      recognition.lang = getSpeechLanguage();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.maxAlternatives = 1;

      recognition.onstart = () => {
        if (!stoppingRef.current) {
          setListening(true);
          setError("");
        }
      };

      recognition.onresult = (event) => {
        let newFinalText = "";
        let newInterimText = "";

        for (let i = event.resultIndex; i < event.results.length; i += 1) {
          const result = event.results[i];
          const transcript = result[0]?.transcript?.trim() || "";

          if (!transcript) continue;

          if (result.isFinal) {
            newFinalText = [newFinalText, transcript]
              .filter(Boolean)
              .join(" ");
          } else {
            newInterimText = [newInterimText, transcript]
              .filter(Boolean)
              .join(" ");
          }
        }

        if (newFinalText) {
          finalTranscriptRef.current = [
            finalTranscriptRef.current,
            newFinalText,
          ]
            .filter(Boolean)
            .join(" ");
        }

        const committed = [
          baseAnswerRef.current,
          finalTranscriptRef.current,
        ]
          .filter(Boolean)
          .join(" ")
          .trim();

        setAnswer(committed);
        setInterimTranscript(newInterimText);
      };

      recognition.onerror = (event) => {
        const nonFatalErrors = new Set([
          "aborted",
          "no-speech",
        ]);

        if (!nonFatalErrors.has(event.error)) {
          listeningRequestedRef.current = false;
          stoppingRef.current = true;
          setListening(false);
          setError(
            `Microphone recognition error: ${event.error}. You can switch to typing.`,
          );
        }
      };

      recognition.onend = () => {
        recognitionRef.current = null;
        setInterimTranscript("");

        if (
          listeningRequestedRef.current &&
          !stoppingRef.current &&
          !submitting
        ) {
          // Chrome/Edge may end recognition after silence even with
          // continuous=true. Restart transparently until the user stops.
          window.setTimeout(() => {
            if (
              listeningRequestedRef.current &&
              !stoppingRef.current &&
              !recognitionRef.current
            ) {
              try {
                const nextRecognition = createRecognition();
                recognitionRef.current = nextRecognition;
                nextRecognition.start();
              } catch {
                listeningRequestedRef.current = false;
                stoppingRef.current = true;
                setListening(false);
                setError(
                  "Microphone recognition stopped unexpectedly. Please start it again.",
                );
              }
            }
          }, 150);
        } else {
          setListening(false);
        }
      };

      return recognition;
    }

    try {
      const recognition = createRecognition();
      recognitionRef.current = recognition;
      recognition.start();
    } catch {
      listeningRequestedRef.current = false;
      stoppingRef.current = true;
      setListening(false);
      setError("Could not start microphone input. Please try again.");
    }
  }

  function stopListening() {
    listeningRequestedRef.current = false;
    stoppingRef.current = true;

    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        try {
          recognitionRef.current.abort();
        } catch {
          // Ignore cleanup failures.
        }
      }
      recognitionRef.current = null;
    }

    setListening(false);
    setInterimTranscript("");
  }

  function switchMode(mode) {
    if (mode === "type" && listening) {
      stopListening();
    }

    setAnswerMode(mode);
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (listening) {
      setError("Stop the microphone before submitting your answer.");
      return;
    }

    const answerToSubmit = answer.trim();

    if (!answerToSubmit) {
      setError("Please enter or speak an answer before submitting.");
      return;
    }

    setSubmitting(true);
    setError("");

    try {
      const response = await fetch(
        `http://localhost:8000/interviews/sessions/${sessionId}/answer`,
        {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ answer_text: answerToSubmit }),
        },
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to submit answer.");
      }

      if (data.status === "completed") {
        navigate(`/interview/${sessionId}/result`);
        return;
      }

      setQuestion({
        session_id: data.session_id,
        question_number: data.current_question,
        total_questions: data.total_questions,
        question_text: data.question.question_text,
        question_type: data.question.question_type,
        status: data.status,
      });

      setAnswer("");
      setInterimTranscript("");
      finalTranscriptRef.current = "";
      baseAnswerRef.current = "";
      setAnswerMode("type");
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return <div className="card empty-state">Loading interview...</div>;
  }

  if (!question) {
    return (
      <div className="alert alert-error">
        {error || "No question available."}
      </div>
    );
  }

  const total = Number(question.total_questions || 1);
  const progress = Math.min(
    100,
    question.total_questions ? (question.question_number / total) * 100 : 0,
  );

  return (
    <div className="interview-shell">
      <div className="interview-header">
        <div>
          <p className="eyebrow">Live Interview</p>
          <h1 className="page-title">AI Interview</h1>
          <p className="page-subtitle">
            Question {question.question_number}
            {question.total_questions ? ` of ${question.total_questions}` : ""}
            {question.current_topic ? ` · ${question.current_topic}` : ""}
          </p>
        </div>
        <span className="badge badge-success">In progress</span>
      </div>

      <div
        className="card"
        style={{
          height: 6,
          overflow: "hidden",
          borderRadius: 999,
          marginBottom: 16,
          border: 0,
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${progress}%`,
            background: "#4f46e5",
            transition: "width .2s ease",
          }}
        />
      </div>

      <section className="card interview-question-card">
        <div className="question-meta">
          <span className="badge badge-primary">
            Question {question.question_number}
          </span>
          <span className="badge badge-neutral">
            {label(question.question_type)}
          </span>
        </div>

        <h2 className="question-title">{question.question_text}</h2>

        <div className="question-audio-row">
          <button
            className="audio-btn"
            type="button"
            disabled={!audioReady}
            onClick={() => audioRef.current?.play()}
          >
            {audioReady ? "▶ Listen to question" : "Preparing voice..."}
          </button>

          {audioError && (
            <span className="muted" style={{ fontSize: 12 }}>
              {audioError}
            </span>
          )}

          <audio
            ref={audioRef}
            preload="auto"
            aria-label="Interview question audio"
          />
        </div>
      </section>

      <section className="card answer-card">
        <div className="card-header">
          <div>
            <h2 className="section-title">Your Answer</h2>
            <p className="section-description">
              Type directly or speak into your microphone. Nothing is submitted
              until you press Submit Answer.
            </p>
          </div>
        </div>

        <div className="answer-mode" role="tablist" aria-label="Answer input mode">
          <button
            className={`answer-mode-btn${answerMode === "type" ? " active" : ""}`}
            type="button"
            onClick={() => switchMode("type")}
          >
            Type Answer
          </button>
          <button
            className={`answer-mode-btn${answerMode === "speak" ? " active" : ""}`}
            type="button"
            onClick={() => switchMode("speak")}
          >
            Speak Answer
          </button>
        </div>

        {answerMode === "type" && (
          <textarea
            className="textarea"
            value={answer}
            onChange={(event) => setAnswer(event.target.value)}
            placeholder="Type your answer here..."
            disabled={submitting}
          />
        )}

        {answerMode === "speak" && (
          <div className="mic-panel">
            {!speechSupported && (
              <div className="alert alert-error" style={{ marginTop: 0 }}>
                Live speech recognition is not supported by this browser.
                Switch to Type Answer or use a supported browser.
              </div>
            )}

            <div className="mic-toolbar">
              <div>
                <div className="mic-status">
                  <span className={`mic-dot${listening ? " live" : ""}`} />
                  {listening
                    ? "Listening — keep speaking"
                    : "Microphone ready"}
                </div>

                <p className="section-description">
                  Your speech appears below while you continue speaking. Stop
                  the microphone when you are finished.
                </p>
              </div>

              <button
                className={`mic-btn${listening ? " stop" : ""}`}
                type="button"
                onClick={listening ? stopListening : startListening}
                disabled={!speechSupported || submitting}
                aria-label={listening ? "Stop recording" : "Start recording"}
              >
                {listening ? "■" : "●"}
              </button>
            </div>

            <div className="transcript-box">
              {answer || (
                <span className="muted">
                  Your live transcript will appear here...
                </span>
              )}
              {interimTranscript && (
                <span className="interim-text"> {interimTranscript}</span>
              )}
            </div>

            {listening && (
              <p className="muted" style={{ marginTop: 8, fontSize: 12 }}>
                Speech recognition uses your browser's English recognition
                engine. Speak naturally and pause briefly between thoughts.
              </p>
            )}
          </div>
        )}

        {error && <div className="alert alert-error">{error}</div>}

        <div className="submit-row">
          <span className="muted" style={{ fontSize: 12 }}>
            {answer.trim().length} characters
          </span>

          <button
            className="primary-btn"
            type="button"
            onClick={handleSubmit}
            disabled={submitting || listening}
          >
            {submitting ? "Evaluating..." : "Submit Answer"}
          </button>
        </div>
      </section>
    </div>
  );
}

function label(value = "") {
  return value ? value.charAt(0).toUpperCase() + value.slice(1) : "";
}

export default Interview;
