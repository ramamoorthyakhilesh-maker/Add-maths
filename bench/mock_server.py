"""A tiny fake OpenRouter for testing bench.py offline. Models behave by name:
mock/good (right answers), mock/latex (right answers written in LaTeX), mock/wrong, mock/noanswer,
mock/flaky (500 and 429 now and then, then works), mock/daylimit (daily limit after 5 requests)."""
import json, re, sys, os, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))
import gen

def build_lookup(seed0=7000, per_cell=2):
    import bench
    look = {}
    for qid in bench.suite(list(gen.GEN), list(gen.LEVELS), per_cell, seed0):
        q = gen.build(qid); look[q["question"]] = q
    return look

def latex(s):
    s = re.sub(r"sqrt\(([^()]*)\)", r"\\sqrt{\1}", s)
    s = re.sub(r"\(([^()]*)\)/\(([^()]*)\)", r"\\frac{\1}{\2}", s)
    s = re.sub(r"(?<![\w)])(-?\d+)/(\d+)", r"\\frac{\1}{\2}", s)
    s = s.replace("pi", r"\pi").replace("<=", r"\le ").replace(">=", r"\ge ")
    s = re.sub(r"\^(\w)", r"^{\1}", s)
    return "$" + s + "$"

class H(BaseHTTPRequestHandler):
    look = {}; counts = {}
    def log_message(self, *a): pass
    def _send(self, code, obj, headers=None):
        b = json.dumps(obj).encode(); self.send_response(code); self.send_header("Content-Type", "application/json")
        for k, v in (headers or {}).items(): self.send_header(k, v)
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        self._send(200, {"data": [{"id": m, "pricing": {"prompt": "0", "completion": "0"}, "context_length": 8192} for m in ("mock/good", "mock/latex", "mock/wrong", "mock/noanswer", "mock/flaky", "mock/daylimit")]})
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.headers.get("Authorization", "") == "Bearer bad-key": return self._send(401, {"error": {"message": "User not found.", "code": 401}})
        m = body["model"]; user = body["messages"][-1]["content"]; n = H.counts[m] = H.counts.get(m, 0) + 1
        q = H.look.get(user)
        if q is None: return self._send(400, {"error": {"message": "unknown question"}})
        ans = gen.ans_str(q)
        if m == "mock/daylimit" and n > 5: return self._send(429, {"error": {"message": "Rate limit exceeded: free-models-per-day"}})
        if m == "mock/flaky" and n % 5 == 0: return self._send(429, {"error": {"message": "slow down"}}, {"Retry-After": "1"})
        if m == "mock/flaky" and n % 3 == 0: return self._send(500, {"error": {"message": "oops"}})
        if m == "mock/wrong": txt = "Working...\nANSWER: 12345"
        elif m == "mock/noanswer": txt = "I think the answer is " + ans
        elif m == "mock/latex": txt = "Step 1...\n**Answer:** " + latex(ans)
        else: txt = "Step 1...\nANSWER: " + ans
        self._send(200, {"choices": [{"message": {"content": txt}}]})

def serve(port=0):
    H.look = build_lookup(); srv = HTTPServer(("127.0.0.1", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start(); return srv

if __name__ == "__main__":
    s = serve(int(sys.argv[1]) if len(sys.argv) > 1 else 8765); print("mock on", s.server_port); threading.Event().wait()
