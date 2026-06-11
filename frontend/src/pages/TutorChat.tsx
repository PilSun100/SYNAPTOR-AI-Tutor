import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, ArrowRight, BookOpen, FileText, MessageSquareText, Send, Sparkles } from 'lucide-react';
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
      setError('Study에서 PDF를 먼저 업로드하거나, 채팅할 자료를 선택하세요.');
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
      const message = caught instanceof Error ? caught.message : '';
      setError(
        message.includes('학습 자료를 찾을 수 없습니다')
          ? '선택한 자료를 찾을 수 없습니다. Study에서 자료를 다시 선택해 주세요.'
          : '답변을 만들지 못했습니다. 자료를 다시 선택하거나 자료에 나온 키워드로 짧게 질문해 주세요.',
      );
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="tutor-chat-page">
      <header className="tutor-chat-header">
        <div>
          <h1>AI Chat</h1>
          <p className="subtitle">업로드한 강의자료를 근거로 개념을 짧게 이해하고, Study에서 직접 설명해봅니다.</p>
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
            자료 설명 모드
          </div>
        </div>

        {!loadingMaterials && materials.length === 0 && (
          <div className="chat-empty-material">
            <MessageSquareText size={34} />
            <strong>채팅할 자료가 없습니다.</strong>
            <p>Study에서 PDF를 먼저 업로드하세요. 업로드한 자료를 기준으로만 설명할 수 있습니다.</p>
            <Link className="glow-btn chat-inline-action" to="/study">
              <BookOpen size={18} />
              Study에서 PDF 업로드
            </Link>
          </div>
        )}

        {selectedMaterial && (
          <div className="chat-material-context">
            <strong>{selectedMaterial.title}</strong>
            <p>{selectedMaterial.preview || '선택한 자료를 기준으로 짧게 질문하고 힌트를 제공합니다.'}</p>
          </div>
        )}

        <div className="chat-thread">
          {selectedMaterial && messages.length === 0 && (
            <div className="chat-welcome">
              <MessageSquareText size={42} className="text-gradient" />
              <strong>자료를 보면서 같이 이해해볼게요.</strong>
              <p>질문을 보내면 업로드한 자료 근거 안에서 짧게 설명하고, 마지막에 Study Room에서 직접 설명해볼 질문을 제안합니다.</p>
              <div className="chat-starter-list">
                {[
                  '이 자료의 핵심 개념을 쉽게 설명해줘',
                  '방금 자료에서 중요한 키워드 3개만 정리해줘',
                  '헷갈리기 쉬운 개념을 비교해서 설명해줘',
                ].map((question) => (
                  <button disabled={sending} key={question} onClick={() => void submitMessage(question)} type="button">
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
                        <button disabled={sending} key={question} onClick={() => void submitMessage(question)} type="button">
                          {question}
                        </button>
                      ))}
                    </div>
                  )}
                  <Link className="chat-study-cta" to="/study">
                    Study Room에서 연습하기
                    <ArrowRight size={16} />
                  </Link>
                </div>
              )}
            </article>
          ))}

          {sending && <div className="chat-loading">업로드한 자료 근거를 확인하고 짧은 설명을 준비하는 중입니다.</div>}
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
            placeholder="예: 이 개념을 쉽게 설명해줘"
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
