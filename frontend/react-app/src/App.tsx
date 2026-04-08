import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ChatPage } from './pages/ChatPage';
import { HomePage } from './pages/HomePage';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<ChatPage />} />
        <Route path="/legacy" element={<HomePage />} />
      </Routes>
    </Router>
  );
}

export default App;
