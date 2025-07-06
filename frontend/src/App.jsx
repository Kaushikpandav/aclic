import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, Bot, User, Loader2, HelpCircle } from 'lucide-react';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showQuestions, setShowQuestions] = useState(false);
  const [isInputFocused, setIsInputFocused] = useState(false);
  // const [threadId, setThreadId] = useState(`thread-${Date.now()}`); // Unique thread ID per session
  const messagesEndRef = useRef(null);

  const suggestedQuestions = [
    "What is the cost to build a small mobile app?",
    "How much for a website with e-commerce features?",
    "What’s the budget for a Flutter app with payment integration?",
    "How much to develop a simple blog platform?",
    "What’s the cost for a custom CRM system?"
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (e) => {
    e.preventDefault();
    
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      text: inputMessage,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString('en-US', { hour12: true, hour: 'numeric', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setShowQuestions(false);

    try {
      console.log("Sending request:", { message: inputMessage, threadId: "1" }); // Debug log
      const response = await axios.post('http://127.0.0.1:8000/query', {
        message: inputMessage
      }, {
        headers: {
          'X-Thread-ID': "1"
        }
      });

      console.log("API Response:", response.data); // Debug log
      const botMessage = {
        id: Date.now() + 1,
        text: response.data.response || 'No response received',
        sender: 'bot',
        timestamp: new Date().toLocaleTimeString('en-US', { hour12: true, hour: 'numeric', minute: '2-digit' }),
        followUpQuestions: response.data.follow_up_questions || [],
        budgetEstimation: response.data.budget_estimation || ''
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error sending message:', error.response ? error.response.data : error.message);
      const errorMessage = {
        id: Date.now() + 1,
        text: error.response?.data?.detail || 'Sorry, I encountered an error. Please try again.',
        sender: 'bot',
        timestamp: new Date().toLocaleTimeString('en-US', { hour12: true, hour: 'numeric', minute: '2-digit' }),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      sendMessage(e);
    }
  };

  const handleQuestionClick = (question) => {
    setInputMessage(question);
    setShowQuestions(false);
  };

  const toggleQuestions = () => {
    setShowQuestions(!showQuestions);
  };

  const handleInputFocus = () => {
    setIsInputFocused(true);
    setShowQuestions(true);
  };

  const handleInputBlur = () => {
    setTimeout(() => {
      setIsInputFocused(false);
      setShowQuestions(false);
    }, 200);
  };

  const startNewThread = () => {
    setThreadId(`thread-${Date.now()}`); // Generate new thread ID
    setMessages([]); // Clear messages for new conversation
  };

  return (
    <div className="min-h-screen flex justify-center items-center p-5">
      <div className="chat-container max-w-2xl w-full bg-white rounded-2xl shadow-xl flex flex-col h-[80vh]">
        {/* Header */}
        <div className="chat-header p-6 border-b border-gray-200">
          <div className="flex items-center justify-center gap-3 mb-2">
            <Bot className="w-6 h-6 text-primary-500" />
            <h1 className="text-2xl font-semibold text-gray-800">Budget Estimation Chatbot</h1>
          </div>
          <p className="text-sm text-gray-500 text-center">Ask about project costs and requirements</p>
          <button
            onClick={startNewThread}
            className="mt-2 px-3 py-1 text-xs bg-primary-100 text-primary-700 hover:bg-primary-200 rounded-full transition-colors duration-200"
          >
            Start New Conversation
          </button>
        </div>

        {/* Messages Container */}
        <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-4">
          {messages.length === 0 && (
            <div className="text-center py-12 text-gray-600">
              <Bot className="w-12 h-12 text-primary-500 mx-auto mb-6" />
              <h2 className="text-2xl font-semibold mb-3 text-gray-800">Welcome to Budget Estimation Chatbot!</h2>
              <p className="text-base leading-relaxed max-w-md mx-auto">
                I'm here to help estimate budgets for your projects. Ask about costs for apps, websites, or other developments!
              </p>
            </div>
          )}
          
          {messages.map((message) => (
            <div
              key={message.id}
              className={`message flex gap-3 ${message.sender === 'user' ? 'flex-row-reverse' : ''} ${message.isError ? 'error' : ''}`}
            >
              <div className="message-avatar p-2">
                {message.sender === 'user' ? <User size={20} className="text-gray-600" /> : <Bot size={20} className="text-primary-500" />}
              </div>
              <div className={`message-content p-4 rounded-2xl ${message.sender === 'user' ? 'bg-primary-100 text-primary-800' : 'bg-gray-50 text-gray-800'} border border-gray-200 max-w-[80%]`}>
                <div className="message-text text-sm">{message.text}</div>
                {message.followUpQuestions && message.followUpQuestions.length > 0 && (
                  <div className="mt-3">
                    <div className="text-xs font-medium text-gray-700 mb-2">Follow-up Questions:</div>
                    <div className="flex flex-wrap gap-2">
                      {message.followUpQuestions.map((question, index) => (
                        <button
                          key={index}
                          onClick={() => handleQuestionClick(question)}
                          className="px-3 py-1.5 text-xs bg-gray-100 text-gray-700 hover:bg-gray-200 rounded-full border border-gray-300 transition-colors duration-200"
                        >
                          {question}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                {message.budgetEstimation && message.budgetEstimation !== 'Unable to estimate budget' && (
                  <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="text-xs font-medium text-blue-700 mb-1">Budget Estimation:</div>
                    <div className="text-sm text-blue-600">{message.budgetEstimation}</div>
                  </div>
                )}
                <div className="text-xs text-gray-500 mt-1 px-1">{message.timestamp}</div>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="message flex gap-3">
              <div className="message-avatar p-2">
                <Bot size={20} className="text-primary-500" />
              </div>
              <div className="message-content p-4 bg-gray-50 rounded-2xl border border-gray-200">
                <div className="flex items-center gap-2 text-gray-600 text-sm">
                  <Loader2 className="w-4 h-4 animate-spin-slow" />
                  <span>Thinking...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input Container */}
        <div className="border-t border-gray-200 bg-white p-6">
          {/* Input Form */}
          <form onSubmit={sendMessage}>
            <div className="flex gap-3 items-end">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                onFocus={handleInputFocus}
                onBlur={handleInputBlur}
                placeholder="Ask about your project budget..."
                disabled={isLoading}
                rows="1"
                className="flex-1 p-3 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
              />
              <button
                type="submit"
                disabled={!inputMessage.trim() || isLoading}
                className="p-3 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:bg-gray-300 transition-colors duration-200"
              >
                <Send size={20} />
              </button>
            </div>
          </form>

          {/* Questions Toggle Button */}
          <div className="mt-3">
            <button
              onClick={toggleQuestions}
              className="inline-flex items-center gap-2 px-3 py-1.5 text-xs bg-gray-100 text-gray-600 rounded-full hover:bg-gray-200 transition-colors duration-200"
            >
              <HelpCircle size={14} />
              {showQuestions ? 'Hide' : 'Show'} Suggestions
            </button>
          </div>

          {/* Suggested Questions */}
          {showQuestions && (
            <div className="mt-3">
              <div className="p-3 bg-gray-50 rounded-lg border border-gray-200 animate-fade-in">
                <h3 className="text-xs font-medium text-gray-700 mb-2">Try asking:</h3>
                <div className="flex flex-wrap gap-2">
                  {suggestedQuestions.map((question, index) => (
                    <button
                      key={index}
                      onClick={() => handleQuestionClick(question)}
                      className="px-3 py-1.5 text-xs bg-white text-gray-600 hover:bg-primary-50 hover:text-primary-600 rounded-full border border-gray-200 transition-colors duration-200"
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;