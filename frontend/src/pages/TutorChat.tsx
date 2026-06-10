import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, BookOpen, FileText, MessageSquareText, Send, Sparkles } from 'lucide-react';
import { getMaterials, sendTutorChatMessage } from '../api/client';
import type { EvidenceSnippet, MaterialSummary, TutorChatResponse } from '../types/api';
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

const chunkTypeLabels: Record<string, string> = {
  text: '텍스트 근거',
  image_description: '이미지/도표 근거',
};

function EvidenceList({ evidence }: { evidence: EvidenceSnippet[] }) {
  if (evidence.length === 0) {
    return (
      <div className="chat-evidence-empty">
        <AlertTriangle size={16} />
        <span>자료에서 충분한 근거를 찾지 못했습니다.</span>
      </div>
    );
  }

  return (
    <div className="chat-evidence-list">
      {evidence.map((item) => (
        <div className="chat-evidence-item" key={`${item.chunk_id}-${item.relevance_score}`}>
          <span>
            p.{item.page_number} · {chunkTypeLabels[item.chunk_type] ?? item.chunk_type} ·{' '}
            {Math.round(item.relevance_score * 100)}%
          </span>
          <p>{item.snippet}</p>
        </div>
      ))}
    </div>
  );
}

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
          <h1>근거 기반 튜터 채팅</h1>
          <p className="subtitle">업로드한 자료의 텍스트와 이미지/도표 근거를 바탕으로 질문하고 학습 방향을 조정합니다.</p>
        </div>
        <Link className="glow-btn" to="/study">
          <BookOpen size={20} />
          학습실
        </Link>
      </header>

      {error && (
        <div className="chat-error">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      <div className="tutor-chat-grid">
        <aside className="glass-panel chat-material-panel">
          <div className="chat-section-title">
            <FileText size={20} />
            <h2>자료 선택</h2>
          </div>

          {loadingMaterials && <p className="chat-muted">자료 목록을 불러오는 중입니다.</p>}
          {!loadingMaterials && materials.length === 0 && (
            <div className="chat-empty-material">
              <MessageSquareText size={34} />
              <strong>채팅할 자료가 없습니다.</strong>
              <p>학습실에서 PDF를 먼저 업로드하면 이곳에서 자료 기반 채팅을 시작할 수 있습니다.</p>
              <Link className="chat-secondary-link" to="/study">자료 업로드하기</Link>
            </div>
          )}

          <div className="chat-material-list">
            {materials.map((material) => (
              <button
                className={material.id === selectedMaterialId ? 'chat-material-item active' : 'chat-material-item'}
                key={material.id}
                onClick={() => {
                  setSelectedMaterialId(material.id);
                  setMessages([]);
                }}
                type="button"
              >
                <strong>{material.title}</strong>
                <span>{material.extracted_text_length.toLocaleString()}자</span>
                <p>{material.preview || '추출된 미리보기가 없습니다.'}</p>
              </button>
            ))}
          </div>
        </aside>

        <section className="glass-panel chat-main-panel">
          <div className="chat-main-heading">
            <div>
              <span>선택 자료</span>
              <h2>{selectedMaterial?.title ?? '자료를 선택하세요'}</h2>
            </div>
            <div className="chat-mode-pill">
              <Sparkles size={16} />
              자료 근거 기반
            </div>
          </div>

          <div className="chat-thread">
            {messages.length === 0 && (
              <div className="chat-welcome">
                <MessageSquareText size={42} className="text-gradient" />
                <strong>자료에 대해 질문해보세요.</strong>
                <p>Brain-Sync는 자료 근거를 먼저 찾고, 정답 설명보다 능동 회상과 자기 설명을 유도합니다.</p>
                <div className="chat-starter-list">
                  {[
                    '이 자료에서 시험에 중요한 개념을 골라줘',
                    '헷갈리기 쉬운 개념을 질문으로 점검해줘',
                    '도표나 그림에서 이해해야 할 부분을 설명해줘',
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
                  <span>{message.role === 'user' ? '나' : 'Brain-Sync Tutor'}</span>
                  <p>{message.content}</p>
                </div>

                {message.response && (
                  <div className="chat-response-meta">
                    <div className="chat-recommendation">
                      <span>{learningModeLabels[message.response.learning_mode] ?? message.response.learning_mode}</span>
                      <strong>{message.response.next_action}</strong>
                    </div>
                    <EvidenceList evidence={message.response.evidence} />
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

            {sending && <div className="chat-loading">근거 chunk를 검색하고 튜터 응답을 구성하는 중입니다.</div>}
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
              placeholder="자료에 기반해 질문하세요. 예: TD와 MC의 차이를 능동 회상 질문으로 점검해줘"
              value={input}
            />
            <button className="glow-btn" disabled={!input.trim() || !selectedMaterialId || sending} type="submit">
              <Send size={18} />
              보내기
            </button>
          </form>
        </section>
      </div>
    </div>
  );
}
