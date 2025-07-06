import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Bot, User, Loader2, HelpCircle } from 'lucide-react';
import { FaArrowUp } from "react-icons/fa";
import * as THREE from 'three';
import aclicLogo from './assets/aclic_logo.png';
import sendIcon from './assets/send.png';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showQuestions, setShowQuestions] = useState(false);
  const [isInputFocused, setIsInputFocused] = useState(false);
  const [askedQuestions, setAskedQuestions] = useState(new Set());
  const [isNearBottom, setIsNearBottom] = useState(true);
  const [userScrolled, setUserScrolled] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const canvasRef = useRef(null);
  const sceneRef = useRef(null);
  const starsRef = useRef(null);

  const suggestedQuestions = [
    "What can you help me with?",
    "Tell me a joke",
    "How do I learn programming?",
    "What's the weather like today?",
    "Can you explain artificial intelligence?"
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const checkIfNearBottom = () => {
    if (!messagesContainerRef.current) return true;
    
    const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current;
    const threshold = 100; // pixels from bottom
    const isNear = scrollHeight - scrollTop - clientHeight < threshold;
    setIsNearBottom(isNear);
    return isNear;
  };

  const handleScroll = () => {
    setUserScrolled(true);
    const isNear = checkIfNearBottom();
    
    if (isNear) {
      setUserScrolled(false);
      setIsExpanded(false);
    } else {
      setIsExpanded(true);
    }
  };

  useEffect(() => {
    if (isNearBottom && !userScrolled) {
      scrollToBottom();
    }
  }, [messages, isNearBottom, userScrolled]);

  useEffect(() => {
    const container = messagesContainerRef.current;
    if (container) {
      container.addEventListener('scroll', handleScroll);
      return () => container.removeEventListener('scroll', handleScroll);
    }
  }, []);

  useEffect(() => {
    if (!canvasRef.current) return;

    let scene, camera, renderer, stars;
    let animationId;

    const init = () => {
      scene = new THREE.Scene();
      camera = new THREE.PerspectiveCamera(60, canvasRef.current.clientWidth / canvasRef.current.clientHeight, 1, 1000);
      camera.position.z = 1;
      camera.rotation.x = Math.PI / 2;

      renderer = new THREE.WebGLRenderer({
        canvas: canvasRef.current,
        alpha: true,
        antialias: true
      });
      renderer.setSize(canvasRef.current.clientWidth, canvasRef.current.clientHeight);
      renderer.setClearColor(0x000000, 0);

      const starGeo = new THREE.BufferGeometry();
      const starCount = 3000;
      const positions = new Float32Array(starCount * 3);
      
      for (let i = 0; i < starCount * 3; i++) {
        positions[i] = (Math.random() - 0.5) * 400;
      }
      
      starGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));

      const starMaterial = new THREE.PointsMaterial({
        color: 0xaaaaaa,
        size: 0.5,
        transparent: true,
        opacity: 0.8
      });

      stars = new THREE.Points(starGeo, starMaterial);
      scene.add(stars);

      sceneRef.current = scene;
      starsRef.current = stars;

      const animate = () => {
        if (stars) {
          stars.rotation.y += 0.0003;
        }
        renderer.render(scene, camera);
        animationId = requestAnimationFrame(animate);
      };

      animate();
    };

    const handleResize = () => {
      if (camera && renderer && canvasRef.current) {
        camera.aspect = canvasRef.current.clientWidth / canvasRef.current.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(canvasRef.current.clientWidth, canvasRef.current.clientHeight);
      }
    };

    init();
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
      if (renderer) {
        renderer.dispose();
      }
    };
  }, []);

  const sendMessage = async (e) => {
    e.preventDefault();
    
    if (!inputMessage.trim() || isLoading) return;

    setAskedQuestions(prev => new Set([...prev, inputMessage.trim()]));

    const userMessage = {
      id: Date.now(),
      text: inputMessage,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit', 
        hour12: true 
      })
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setShowQuestions(false);

    try {
      const response = await axios.post('http://127.0.0.1:8000/query', {
        message: inputMessage
      });

      const botMessage = {
        id: Date.now() + 1,
        text: response.data.response || 'No response received',
        sender: 'bot',
        timestamp: new Date().toLocaleTimeString('en-US', { 
          hour: 'numeric', 
          minute: '2-digit', 
          hour12: true 
        }),
        followUpQuestions: response.data.follow_up_questions || [],
        budgetEstimation: response.data.budget_estimation || ''
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      
      let errorText = 'Sorry, I encountered an error. Please try again.';
      
      if (error.response && error.response.data) {
        if (error.response.data.detail) {
          errorText = error.response.data.detail;
        } else if (error.response.data.message) {
          errorText = error.response.data.message;
        }
      } else if (error.message) {
        errorText = `Connection error: ${error.message}`;
      }
      
      const errorMessage = {
        id: Date.now() + 1,
        text: errorText,
        sender: 'bot',
        timestamp: new Date().toLocaleTimeString('en-US', { 
          hour: 'numeric', 
          minute: '2-digit', 
          hour12: true 
        }),
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
    setAskedQuestions(prev => new Set([...prev, question.trim()]));
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

  return (
    <div className={`min-h-screen flex justify-center items-center p-5 transition-all duration-500 ease-in-out ${isExpanded ? 'pt-8' : ''}`}>
      <div className={`chat-container ${isExpanded ? 'expanded' : ''}`}>
        {/* Animated Star Background Canvas */}
        <canvas 
          ref={canvasRef}
          className="absolute inset-0 w-full h-full pointer-events-none"
          style={{ zIndex: 0 }}
        />
        {/* Header */}
        <div className="chat-header">
          <div className="flex items-center justify-between px-4">
            <div className="flex items-center gap-3">
              <img src={aclicLogo} alt="Aclic Logo" className="w-8 h-8" />
              <h1 className="text-2xl font-bold text-white">Management Chatbot</h1>
            </div>
            {/* <div className="text-sm text-gray-300">v1.0.0</div> */}
          </div>
          <p className="text-sm text-gray-400 mt-1 px-4">
            Powered by <span className="font-semibold text-cyan-300">Aclic</span>
          </p>
        </div>

        {/* Messages Container */}
        <div 
          ref={messagesContainerRef}
          className="flex-1 overflow-y-auto p-6 flex flex-col gap-4 relative" 
          style={{ zIndex: 1 }}
        >
          {messages.length === 0 && (
            <div className="text-center py-12 text-gray-300">
              <Bot className="w-12 h-12 text-cyan-400 mx-auto mb-6" />
              <h2 className="text-2xl font-semibold mb-3 text-white">Welcome to Management Chatbot!</h2>
              <p className="text-base leading-relaxed max-w-md mx-auto text-gray-300">
                I'm here to help you with any questions you might have. Feel free to ask me anything!
              </p>
            </div>
          )}
          
          {messages.map((message) => (
            <div
              key={message.id}
              className={`message ${message.sender} ${message.isError ? 'error' : ''}`}
            >
              <div className="message-avatar">
                {message.sender === 'user' ? <User size={20} /> : <Bot size={20} />}
              </div>
              <div className="message-content">
                <div className="message-text">{message.text}</div>
                
                {message.budgetEstimation && message.budgetEstimation !== 'Unable to refine budget estimation' && (
                  <div className="mt-2 p-2 bg-blue-900/50 border border-blue-600 rounded-lg">
                    <div className="text-xs font-medium text-blue-300 mb-1">Budget Estimation:</div>
                    <div className="text-sm text-blue-200">{message.budgetEstimation}</div>
                  </div>
                )}
                
                {message.followUpQuestions && message.followUpQuestions.length > 0 && (
                  <div className="mt-3">
                    <div className="text-xs font-medium text-gray-300 mb-2">Follow-up questions:</div>
                    <div className="flex flex-wrap gap-2">
                      {message.followUpQuestions.map((question, index) => {
                        const isAsked = askedQuestions.has(question.trim());
                        return (
                          <button
                            key={index}
                            onClick={() => handleQuestionClick(question)}
                            className={`px-3 py-1.5 text-xs rounded-full border transition-colors duration-200 ${
                              isAsked 
                                ? 'bg-gray-600 text-gray-400 border-gray-500 cursor-not-allowed' 
                                : 'bg-purple-700 text-gray-200 hover:bg-purple-600 border-purple-600'
                            }`}
                            disabled={isAsked}
                          >
                            {question}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
                
                <div className="text-xs text-gray-400 mt-1 px-1">
                  {message.timestamp}
                </div>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="message bot">
              <div className="message-avatar">
                <Bot size={20} />
              </div>
              <div className="message-content">
                <div className="flex items-center gap-2 px-4 py-3 bg-gray-800/90 rounded-2xl rounded-bl-md border border-gray-600 text-gray-300 text-sm backdrop-blur-sm">
                  <Loader2 className="w-4 h-4 animate-spin-slow" />
                  <span>Thinking...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input Container */}
        <div className="border border-gray-700 bg-gray-900/95 relative" style={{ zIndex: 1 }}>
          <div className="px-6 pt-6 pb-3">
            <div className="flex gap-3 items-end">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                onFocus={handleInputFocus}
                onBlur={handleInputBlur}
                placeholder="Type your message here..."
                disabled={isLoading}
                rows="1"
                className="input-field"
              />
              <button
                type="button"
                onClick={sendMessage}
                disabled={!inputMessage.trim() || isLoading}
                className="send-button"
              >
                {/* <img src={sendIcon} alt="Send" className="w-5 h-5" /> */}
                <FaArrowUp size={20} />
              </button>
            </div>
          </div>

          <div className="px-6 pb-2">
            <button
              onClick={toggleQuestions}
              className="inline-flex items-center gap-2 px-3 py-1.5 text-xs bg-gray-700 text-gray-300 rounded-full hover:bg-gray-600 transition-colors duration-200"
            >
              <HelpCircle size={14} />
              {showQuestions ? 'Hide' : 'Show'} Suggestions
            </button>
          </div>

          {showQuestions && (
            <div className="px-6 pb-6">
              <div className="p-3 bg-gray-800/50 rounded-lg border border-gray-600 animate-fade-in">
                <h3 className="text-xs font-medium text-gray-300 mb-2">Try asking:</h3>
                <div className="flex flex-wrap gap-2">
                  {suggestedQuestions.map((question, index) => {
                    const isAsked = askedQuestions.has(question.trim());
                    return (
                      <button
                        key={index}
                        onClick={() => handleQuestionClick(question)}
                        className={`px-3 py-1.5 text-xs rounded-full border transition-colors duration-200 ${
                          isAsked 
                            ? 'bg-gray-600 text-gray-400 border-gray-500 cursor-not-allowed' 
                            : 'bg-gray-700 text-gray-200 hover:bg-gray-600 hover:text-white border-gray-600'
                        }`}
                        disabled={isAsked}
                      >
                        {question}
                      </button>
                    );
                  })}
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