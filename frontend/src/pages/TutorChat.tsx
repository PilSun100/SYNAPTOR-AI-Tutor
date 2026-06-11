import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, BookOpen, FileText, MessageSquareText, Send, Sparkles } from 'lucide-react';
import { getMaterials, sendTutorChatMessage } from '../api/client';
import type { MaterialSummary, TutorChatResponse } from '../types/api';
import './TutorChat.css';

type ChatTurn = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  response?: TutorChatResponse;
};

const learningModeLabels: Record<string, string> = {
  active_recall: 'Active Recall',
  feynman_check: 'Feynman Check',
  misconception_repair: 'Misconception Repair',
  evidence_check: 'Evidence Check',
  example_first: 'Example First',
};

export function TutorChat() {
  const [materials, setMaterials] = useState<MaterialSummary[]>([]);
  const [selectedMaterialId, setSelectedMaterialId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatTurn[]>([]);
  const [input, setInput] = useState('');
  const [loadingMaterials, setLoadingMaterials] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');

  const selectedMaterial = useMemo(
    () => materials.find((material) => material.id === selectedMaterialId) ?? null,
    [materials, selectedMaterialId],
  );

  useEffect(() => {
    let mounted = true;

    async function loadMaterials() {
      setLoadingMaterials(true);
      setError('');
      try {
        const response = await getMaterials();
        if (!mounted) {
          return;
        }
        setMaterials(response.materials);
        setSelectedMaterialId((current) => current ?? response.materials[0]?.id ?? null);
      } catch (caught) {
        if (mounted) {
          setError(caught instanceof Error ? caught.message : '자료 목록을 불러오지 못했습니다.');
        }
      } finally {
        if (mounted) {
          setLoadingMaterials(false);
        }
      }
    }

    void loadMaterials();

    return () => {
      mounted = false;
    };
  }, []);

  const submitMessage = async (messageText = input) => {
    const trimmed = messageText.trim();
    if (!trimmed || sending) {
      return;
    }
    if (!selectedMaterialId) {
      setError('먼저 채팅할 학습 자료를 선택하세요.');
      return;
    }

    const userTurn: ChatTurn = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: trimmed,
    };

    setMessages((current) => [...current, userTurn]);
    setInput('');
    setError('');
    setSending(true);

    try {
      const response = await sendTutorChatMessage(selectedMaterialId, trimmed);
      const assistantTurn: ChatTurn = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.reply,
        response,
      };
      setMessages((current) => [...current, assistantTurn]);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '튜터 응답을 생성하지 못했습니다.');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="tutor-chat-page">
      <header className="tutor-chat-header">
        <div>
          <h1>AI Chat</h1>
          <p className="subtitle">정답을 바로 받기보다, 자료를 근거로 한 질문과 힌트로 먼저 생각해봅니다.</p>
        </div>
        <Link className="glow-btn" to="/study">
          <BookOpen size={20} />
          Study
        </Link>
      </header>

      {error && (
        <div className="chat-error">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      <section className="glass-panel chat-main-panel">
        <div className="chat-context-bar">
          <label>
            <FileText size={18} />
            <select
              disabled={loadingMaterials || materials.length === 0}
              onChange={(event) => {
                setSelectedMaterialId(Number(event.target.value));
                setMessages([]);
              }}
              value={selectedMaterialId ?? ''}
            >
              <option value="">{loadingMaterials ? '자료를 불러오는 중' : '자료 선택'}</option>
              {materials.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.title}
                </option>
              ))}
            </select>
          </label>
          <div className="chat-mode-pill">
            <Sparkles size={16} />
            Socratic Coach
          </div>
        </div>

        {!loadingMaterials && materials.length === 0 && (
          <div className="chat-empty-material">
            <MessageSquareText size={34} />
            <strong>채팅할 자료가 없습니다.</strong>
            <p>Study에서 PDF를 먼저 업로드하면 자료 기반 코칭을 시작할 수 있습니다.</p>
            <Link className="chat-secondary-link" to="/study">자료 업로드하기</Link>
          </div>
        )}

        {selectedMaterial && (
          <div className="chat-material-context">
            <strong>{selectedMaterial.title}</strong>
            <p>{selectedMaterial.preview || '선택한 자료를 기준으로 짧게 질문하고 힌트를 제공합니다.'}</p>
          </div>
        )}

        <div className="chat-thread">
          {messages.length === 0 && (
            <div className="chat-welcome">
              <MessageSquareText size={42} className="text-gradient" />
              <strong>먼저 생각하게 도와줄게요.</strong>
              <p>질문을 보내면 AI가 바로 정답을 길게 설명하지 않고, 자료 근거 안에서 회상 질문과 단서를 제공합니다.</p>
              <div className="chat-starter-list">
                {[
                  '이 자료에서 중요한 개념을 하나 질문으로 점검해줘',
                  '내가 먼저 떠올릴 수 있게 작은 힌트부터 줘',
                  '헷갈리기 쉬운 두 개념을 비교 질문으로 만들어줘',
                ].map((question) => (
                  <button key={question} onClick={() => void submitMessage(question)} type="button">
                    {question}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message) => (
            <article className={`chat-turn ${message.role}`} key={message.id}>
              <div className="chat-bubble">
                <span>{message.role === 'user' ? '나' : 'AI Coach'}</span>
                <p>{message.content}</p>
              </div>

              {message.response && (
                <div className="chat-response-meta">
                  <div className="chat-recommendation">
                    <span>{learningModeLabels[message.response.learning_mode] ?? message.response.learning_mode}</span>
                    <strong>{message.response.next_action}</strong>
                  </div>
                  {message.response.suggested_questions.length > 0 && (
                    <div className="chat-suggestions">
                      {message.response.suggested_questions.map((question) => (
                        <button key={question} onClick={() => void submitMessage(question)} type="button">
                          {question}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </article>
          ))}

          {sending && <div className="chat-loading">자료 근거를 보고 짧은 코칭 응답을 준비하는 중입니다.</div>}
        </div>

        <form
          className="chat-input-bar"
          onSubmit={(event) => {
            event.preventDefault();
            void submitMessage();
          }}
        >
          <input
            disabled={!selectedMaterialId || sending}
            onChange={(event) => setInput(event.target.value)}
            placeholder="예: 바로 답 말고 내가 떠올릴 수 있게 힌트부터 줘"
            value={input}
          />
          <button className="glow-btn" disabled={!input.trim() || !selectedMaterialId || sending} type="submit">
            <Send size={18} />
            보내기
          </button>
        </form>
      </section>
    </div>
  );
}
