import React from 'react';
import ReactDOM from 'react-dom/client';
import { CONFIG } from './config/env';

const API = CONFIG.API_BASE_URL;

interface User {
  id: number;
  email: string;
  username: string;
}

interface Post {
  id: string;
  title: string;
  content: string;
  url: string;
  score: number;
  num_comments: number;
  subreddit: string;
}

function App() {
  const [user, setUser] = React.useState<User | null>(null);
  const [token, setToken] = React.useState<string>('');
  const [email, setEmail] = React.useState('shortsubjayfire@gmail.com');
  const [password, setPassword] = React.useState('cuiJY20130111');
  const [posts, setPosts] = React.useState<Post[]>([]);
  const [selectedPost, setSelectedPost] = React.useState<Post | null>(null);
  const [comment, setComment] = React.useState('');
  const [generatedComment, setGeneratedComment] = React.useState('');
  const [status, setStatus] = React.useState('');
  const [loading, setLoading] = React.useState(false);

  const login = async () => {
    try {
      const r = await fetch(`${API}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const d = await r.json();
      if (d.access_token) {
        setToken(d.access_token);
        setUser(d.user);
        setStatus(`Logged in as ${d.user.email}`);
        fetchPosts();
      } else {
        setStatus('Login failed: ' + d.detail);
      }
    } catch(e: any) {
      setStatus('Error: ' + e.message);
    }
  };

  const fetchPosts = async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/style/posts?subreddit=askreddit&limit=5`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      const d = await r.json();
      setPosts(d.list || []);
    } catch(e: any) {
      setStatus('Error fetching posts: ' + e.message);
    }
    setLoading(false);
  };

  const generateComment = async () => {
    if (!selectedPost) {
      alert('Please select a post first');
      return;
    }
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/comment/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          post_title: selectedPost.title,
          post_content: selectedPost.content,
          use_style: true
        })
      });
      const d = await r.json();
      if (d.comment) {
        setGeneratedComment(d.comment);
        setStatus('');
      } else {
        setStatus('Generation failed: ' + d.message);
      }
    } catch(e: any) {
      setStatus('Error: ' + e.message);
    }
    setLoading(false);
  };

  return (
    <div style={{ width: '400px', padding: '16px', fontFamily: 'system-ui' }}>
      <h2 style={{ color: '#ff4500', marginBottom: '16px' }}>Reddit Comment Assistant</h2>

      {!user ? (
        <div style={{ marginBottom: '16px' }}>
          <input
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="Email"
            style={{ width: '100%', marginBottom: '8px', padding: '8px' }}
          />
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="Password"
            style={{ width: '100%', marginBottom: '8px', padding: '8px' }}
          />
          <button onClick={login} style={{ width: '100%', padding: '8px', background: '#ff4500', color: 'white', border: 'none', cursor: 'pointer' }}>
            Login
          </button>
        </div>
      ) : (
        <div style={{ marginBottom: '16px' }}>
          <p style={{ fontSize: '12px', color: '#888' }}>Logged in as {user.email}</p>
          <button onClick={fetchPosts} style={{ padding: '8px', background: '#555', color: 'white', border: 'none', cursor: 'pointer' }}>
            Refresh Posts
          </button>
        </div>
      )}

      {status && <p style={{ fontSize: '12px', marginBottom: '8px' }}>{status}</p>}

      {loading && <p>Loading...</p>}

      {posts.length > 0 && (
        <div style={{ maxHeight: '200px', overflowY: 'auto', marginBottom: '16px' }}>
          {posts.map((post, i) => (
            <div
              key={post.id}
              onClick={() => setSelectedPost(post)}
              style={{
                padding: '8px',
                marginBottom: '4px',
                background: selectedPost?.id === post.id ? '#555' : '#333',
                cursor: 'pointer',
                borderRadius: '4px'
              }}
            >
              <div style={{ fontSize: '12px', fontWeight: 'bold' }}>{post.title.substring(0, 50)}...</div>
              <div style={{ fontSize: '10px', color: '#888' }}>r/{post.subreddit} • {post.score} votes</div>
            </div>
          ))}
        </div>
      )}

      {selectedPost && (
        <div style={{ marginBottom: '16px' }}>
          <h3 style={{ fontSize: '14px', marginBottom: '8px' }}>Selected Post</h3>
          <p style={{ fontSize: '12px', background: '#222', padding: '8px', borderRadius: '4px' }}>
            {selectedPost.title}
          </p>
          <textarea
            value={comment}
            onChange={e => setComment(e.target.value)}
            placeholder="Write your comment style sample..."
            style={{ width: '100%', height: '60px', marginTop: '8px', padding: '8px' }}
          />
          <button
            onClick={generateComment}
            disabled={loading}
            style={{ marginTop: '8px', padding: '8px 16px', background: '#ff4500', color: 'white', border: 'none', cursor: 'pointer' }}
          >
            Generate Comment
          </button>
        </div>
      )}

      {generatedComment && (
        <div style={{ marginTop: '16px', padding: '12px', background: '#1a1a2e', borderRadius: '8px' }}>
          <h3 style={{ fontSize: '14px', marginBottom: '8px' }}>Generated Comment</h3>
          <p style={{ fontSize: '14px', whiteSpace: 'pre-wrap' }}>{generatedComment}</p>
        </div>
      )}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('app')!).render(<App />);