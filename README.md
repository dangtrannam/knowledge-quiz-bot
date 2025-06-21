# 🧠 Knowledge Quiz Bot

> Your AI-powered learning companion, inspired by Google's NotebookLM

A sophisticated AI platform that transforms your documents into interactive learning experiences. Upload PDFs, text files, or Word documents, then either chat with your content or take personalized quizzes to test and reinforce your knowledge.

## 🌟 Features

### 📚 **Smart Document Processing**
- **Multiple formats**: PDF, TXT, DOCX support
- **Intelligent chunking**: Optimized text segmentation
- **Vector embeddings**: Semantic search capabilities
- **Source citations**: Track information back to original documents

### 💬 **Interactive Chat Interface**
- **Document selection**: Chat with specific files or all documents
- **Contextual responses**: AI answers based only on your uploaded content
- **Source citations**: See exactly which documents inform each response
- **Conversation starters**: Get helpful suggestions to begin your chat

### 🎯 **Adaptive Quiz Generation**
- **Multiple question types**: Multiple choice, True/False, Short answer
- **Difficulty adaptation**: AI adjusts based on your performance
- **Context-aware**: Questions generated from your specific content
- **Detailed explanations**: Learn from both correct and incorrect answers

### 📊 **Progress Tracking**
- **Real-time scoring**: Track accuracy and improvement
- **Performance analytics**: Understand your learning patterns
- **Grade calculation**: Get meaningful feedback on your progress
- **History tracking**: Review past quiz sessions

### 🎨 **Modern Interface**
- **Clean design**: Inspired by NotebookLM's user experience
- **Responsive layout**: Works on desktop and mobile
- **Interactive elements**: Smooth animations and feedback
- **Intuitive navigation**: Easy-to-use sidebar controls

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/knowledge-quiz-bot.git
   cd knowledge-quiz-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run app.py
   ```

4. **Open your browser**
   Navigate to `http://localhost:8501`

## 📖 How to Use

### 1. **Configure API Settings**
- Enter your OpenAI API key in the sidebar
- **Advanced Settings**: Optionally configure custom base URL and select AI model
- **Model Selection**: Choose from predefined models or enter custom model names
  - **Predefined**: GPT-3.5 Turbo, GPT-4, GPT-4 Turbo, GPT-4o, GPT-4o Mini, and more
  - **Custom**: Enter any model name (e.g., `gpt-4-1106-preview`, `claude-3-opus`, custom models)
- Support for OpenAI-compatible APIs by setting custom base URL

### 2. **Upload Documents**
- Click "Choose files" to upload your learning materials
- Supported formats: PDF, TXT, DOCX
- Multiple files can be uploaded simultaneously

### 3. **Build Knowledge Base**
- Click "📖 Build Knowledge Base" to process your documents
- AI will analyze and index your content for both chat and quiz features

### 4. **Choose Your Mode**
- **💬 Chat Mode**: Have interactive conversations with your documents
- **🎯 Quiz Mode**: Test your knowledge with AI-generated questions

#### For Chat Mode:
### 5a. **Select Documents**
- Choose specific documents or select "All Documents" to chat with everything
- See detailed information about your selected content

### 6a. **Start Chatting**
- Click "💬 Start Chat" to begin your conversation
- Ask questions about your documents and get contextual responses
- Use conversation starters for inspiration

#### For Quiz Mode:
### 5b. **Configure Quiz Settings**
- **Quiz Type**: Choose from Multiple Choice, True/False, Short Answer, or Mixed
- **Difficulty**: Select Easy, Medium, Hard, or Adaptive
- **Number of Questions**: Set anywhere from 5 to 50 questions

### 6b. **Take the Quiz**
- Click "🚀 Start Quiz" to begin
- Answer questions and receive immediate feedback
- View explanations and source citations for each answer

### 7. **Review Results**
- See your final score and grade (Quiz Mode)
- Get personalized feedback on your performance
- Option to retake quiz or switch to chat mode

## 🎮 Try the Demo

Don't have documents ready? Try our built-in demo:

1. Click "🎮 Try with Sample Content" in the upload section
2. Select "Load Demo: AI & Machine Learning"
3. Start taking quizzes immediately!

## 🏗️ Architecture

The project follows a modular architecture inspired by modern AI applications:

```
knowledge-quiz-bot/
├── app.py                 # Main Streamlit application
├── quiz_bot.py           # Core quiz generation logic
├── chat_bot.py           # Interactive chat functionality
├── knowledge_manager.py   # Document processing and vector storage
├── utils.py              # Helper functions and UI components
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

### Core Components

- **KnowledgeManager**: Handles document ingestion, processing, and vector database management
- **QuizBot**: Generates questions using LangChain and OpenAI, manages difficulty adaptation
- **ChatBot**: Provides interactive chat interface with document selection and contextual responses
- **Streamlit UI**: Provides an intuitive interface similar to NotebookLM's design

## 🛠️ Technical Details

### AI Models Used
- **OpenAI GPT-4o-mini**: For question generation and short answer evaluation
- **all-MiniLM-L6-v2**: For semantic document search and retrieval
- **ChromaDB**: Vector database for efficient similarity search

### Question Generation Process
1. **Context Retrieval**: Randomly select relevant document chunks
2. **Prompt Engineering**: Use specialized prompts for each question type
3. **JSON Parsing**: Structure questions with metadata and explanations
4. **Fallback Handling**: Graceful error recovery with backup questions

### Adaptive Difficulty
- Tracks recent performance (last 3 questions)
- Automatically adjusts difficulty based on success rate
- Provides personalized learning experience

## 🎯 Use Cases

### **Students**
- Study for exams using course materials
- Test comprehension of textbooks and papers
- Create practice quizzes from lecture notes

### **Professionals**
- Review training materials and documentation
- Test knowledge of company policies and procedures
- Prepare for certifications and assessments

### **Educators**
- Generate quiz questions from curriculum content
- Create assessments based on reading materials
- Provide students with self-study tools

### **Researchers**
- Test understanding of research papers
- Review literature and extract key concepts
- Validate comprehension of complex topics

## 🔧 Configuration Options

### Environment Variables
```bash
OPENAI_API_KEY=your_api_key_here
```

### Customizable Settings
- **AI Model Selection**: 
  - Predefined models: GPT-3.5 Turbo, GPT-4, GPT-4 Turbo, GPT-4o, GPT-4o Mini
  - Custom models: Enter any model name for latest OpenAI models or third-party APIs
- **Custom Base URL**: Support for OpenAI-compatible APIs (Azure OpenAI, Anthropic, Local models, etc.)
- **Model Validation**: Built-in warnings for common model name issues
- **Chunk Size**: Adjust document splitting (default: 1000 characters)
- **Chunk Overlap**: Control context preservation (default: 200 characters)
- **Vector DB**: Persistent storage location (default: ./chroma_db)
- **Question History**: Number of questions to track (default: 20)

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Setup
```bash
# Clone your fork
git clone https://github.com/your-username/knowledge-quiz-bot.git

# Install development dependencies
pip install -r requirements.txt

# Run tests (when available)
pytest

# Start development server
streamlit run app.py
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google NotebookLM**: Inspiration for the user experience and document processing approach
- **LangChain**: Powerful framework for building LLM applications
- **Streamlit**: Excellent platform for creating ML web applications
- **OpenAI**: Advanced language models that power the question generation

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/knowledge-quiz-bot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/knowledge-quiz-bot/discussions)
- **Email**: your-email@example.com

## 🗺️ Roadmap

### Upcoming Features
- [ ] **Multi-language support**: Questions and interface in multiple languages
- [ ] **Advanced analytics**: Detailed learning progress insights
- [ ] **Collaborative features**: Share quiz sessions with others
- [ ] **Custom prompts**: User-defined question generation templates
- [ ] **Export functionality**: Save quizzes as PDF or other formats
- [ ] **Integration APIs**: Connect with learning management systems

### Long-term Vision
- [ ] **Voice interactions**: Audio questions and responses
- [ ] **Mobile app**: Native iOS and Android applications
- [ ] **Advanced AI models**: Support for different LLM providers
- [ ] **Gamification**: Badges, streaks, and achievement systems

---

Made with ❤️ by developers who love learning and AI

**Star ⭐ this repo if you find it useful!** 