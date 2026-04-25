import { useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";

const emptyForm = {
  personal_name: "",
  personal_email: "",
  personal_phone: "",
  business_name: "",
  business_type: "freelancer",
  expected_monthly_volume_usd: "",
  pan_document: null,
  aadhaar_document: null,
  bank_statement_document: null,
};

async function apiRequest(path, method = "GET", token = "", body = null, isFormData = false) {
  const headers = {};
  if (token) headers.Authorization = `Token ${token}`;
  if (!isFormData) headers["Content-Type"] = "application/json";

  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? (isFormData ? body : JSON.stringify(body)) : null,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error?.message || "Request failed");
  }
  return data;
}

function App() {
  const [authMode, setAuthMode] = useState("login");
  const [credentials, setCredentials] = useState({
    username: "",
    password: "",
    email: "",
    role: "merchant",
  });
  const [session, setSession] = useState({ token: "", role: "", username: "" });
  const [formState, setFormState] = useState(emptyForm);
  const [submission, setSubmission] = useState(null);
  const [queue, setQueue] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [selectedSubmission, setSelectedSubmission] = useState(null);
  const [reviewReason, setReviewReason] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const isLoggedIn = Boolean(session.token);
  const isReviewer = session.role === "reviewer";

  const fillPercent = useMemo(() => {
    const fields = [
      "personal_name",
      "personal_email",
      "personal_phone",
      "business_name",
      "business_type",
      "expected_monthly_volume_usd",
    ];
    const completeCount = fields.filter((f) => formState[f]).length;
    return Math.round((completeCount / fields.length) * 100);
  }, [formState]);

  const updateField = (e) => {
    const { name, value, files } = e.target;
    setFormState((prev) => ({ ...prev, [name]: files ? files[0] : value }));
  };

  const login = async () => {
    try {
      setError("");
      setMessage("");
      const payload = await apiRequest("/auth/login/", "POST", "", {
        username: credentials.username,
        password: credentials.password,
      });
      setSession(payload);
      setMessage("Logged in successfully.");
    } catch (err) {
      setError(err.message);
    }
  };

  const signup = async () => {
    try {
      setError("");
      setMessage("");
      const payload = await apiRequest("/auth/signup/", "POST", "", credentials);
      setSession({ token: payload.token, role: payload.user.role, username: payload.user.username });
      setMessage("Signup successful.");
    } catch (err) {
      setError(err.message);
    }
  };

  const loadMerchantSubmission = async () => {
    try {
      const data = await apiRequest("/merchant/submission/", "GET", session.token);
      setSubmission(data);
      setFormState((prev) => ({ ...prev, ...data }));
    } catch (err) {
      setError(err.message);
    }
  };

  const saveDraft = async () => {
    try {
      setError("");
      const fd = new FormData();
      Object.entries(formState).forEach(([k, v]) => {
        if (v !== null && v !== "") fd.append(k, v);
      });
      const data = await apiRequest("/merchant/submission/", "PATCH", session.token, fd, true);
      setSubmission(data);
      setMessage("Draft saved.");
    } catch (err) {
      setError(err.message);
    }
  };

  const submitKYC = async () => {
    try {
      await saveDraft();
      const data = await apiRequest("/merchant/submission/submit/", "POST", session.token);
      setSubmission(data);
      setMessage("Submission sent for review.");
    } catch (err) {
      setError(err.message);
    }
  };

  const loadQueue = async () => {
    try {
      const [queueData, metricData] = await Promise.all([
        apiRequest("/reviewer/queue/", "GET", session.token),
        apiRequest("/reviewer/metrics/", "GET", session.token),
      ]);
      setQueue(queueData);
      setMetrics(metricData);
    } catch (err) {
      setError(err.message);
    }
  };

  const loadSubmissionDetail = async (id) => {
    try {
      const data = await apiRequest(`/reviewer/submissions/${id}/`, "GET", session.token);
      setSelectedSubmission(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const takeAction = async (action) => {
    if (!selectedSubmission) return;
    try {
      await apiRequest(`/reviewer/submissions/${selectedSubmission.id}/action/`, "POST", session.token, {
        action,
        reason: reviewReason,
      });
      setMessage(`Action ${action} completed.`);
      setReviewReason("");
      await loadQueue();
      await loadSubmissionDetail(selectedSubmission.id);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="mx-auto min-h-screen max-w-6xl p-6">
      <h1 className="mb-4 text-3xl font-bold">Playto KYC Pipeline</h1>
      {message && <div className="mb-3 rounded bg-green-100 p-3 text-green-800">{message}</div>}
      {error && <div className="mb-3 rounded bg-red-100 p-3 text-red-800">{error}</div>}

      {!isLoggedIn ? (
        <div className="rounded bg-white p-6 shadow">
          <div className="mb-4 flex gap-2">
            <button className="rounded bg-slate-800 px-4 py-2 text-white" onClick={() => setAuthMode("login")}>
              Login
            </button>
            <button className="rounded bg-slate-600 px-4 py-2 text-white" onClick={() => setAuthMode("signup")}>
              Signup
            </button>
          </div>
          <div className="grid gap-3">
            <input className="rounded border p-2" placeholder="Username" name="username" onChange={(e) => setCredentials((s) => ({ ...s, username: e.target.value }))} />
            <input className="rounded border p-2" placeholder="Password" type="password" name="password" onChange={(e) => setCredentials((s) => ({ ...s, password: e.target.value }))} />
            {authMode === "signup" && (
              <>
                <input className="rounded border p-2" placeholder="Email" name="email" onChange={(e) => setCredentials((s) => ({ ...s, email: e.target.value }))} />
                <select className="rounded border p-2" name="role" onChange={(e) => setCredentials((s) => ({ ...s, role: e.target.value }))}>
                  <option value="merchant">Merchant</option>
                  <option value="reviewer">Reviewer</option>
                </select>
              </>
            )}
            <button className="rounded bg-blue-600 px-4 py-2 text-white" onClick={authMode === "login" ? login : signup}>
              {authMode === "login" ? "Login" : "Create Account"}
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="rounded bg-white p-4 shadow">
            <p>
              Logged in as <b>{session.username}</b> ({session.role})
            </p>
          </div>

          {!isReviewer ? (
            <div className="space-y-4">
              <div className="rounded bg-white p-4 shadow">
                <div className="mb-2 flex items-center justify-between">
                  <h2 className="text-xl font-semibold">Merchant KYC Form</h2>
                  <button className="rounded bg-indigo-600 px-3 py-2 text-white" onClick={loadMerchantSubmission}>
                    Load Existing
                  </button>
                </div>
                <p className="mb-3 text-sm text-gray-600">Completion: {fillPercent}%</p>
                <div className="grid gap-3 md:grid-cols-2">
                  <input className="rounded border p-2" name="personal_name" placeholder="Personal Name" value={formState.personal_name || ""} onChange={updateField} />
                  <input className="rounded border p-2" name="personal_email" placeholder="Personal Email" value={formState.personal_email || ""} onChange={updateField} />
                  <input className="rounded border p-2" name="personal_phone" placeholder="Personal Phone" value={formState.personal_phone || ""} onChange={updateField} />
                  <input className="rounded border p-2" name="business_name" placeholder="Business Name" value={formState.business_name || ""} onChange={updateField} />
                  <select className="rounded border p-2" name="business_type" value={formState.business_type || "freelancer"} onChange={updateField}>
                    <option value="freelancer">Freelancer</option>
                    <option value="agency">Agency</option>
                    <option value="ecommerce">Ecommerce</option>
                    <option value="saas">SaaS</option>
                    <option value="other">Other</option>
                  </select>
                  <input className="rounded border p-2" name="expected_monthly_volume_usd" type="number" placeholder="Expected monthly volume (USD)" value={formState.expected_monthly_volume_usd || ""} onChange={updateField} />
                  <input className="rounded border p-2" name="pan_document" type="file" onChange={updateField} />
                  <input className="rounded border p-2" name="aadhaar_document" type="file" onChange={updateField} />
                  <input className="rounded border p-2" name="bank_statement_document" type="file" onChange={updateField} />
                </div>
                <div className="mt-4 flex gap-2">
                  <button className="rounded bg-slate-700 px-4 py-2 text-white" onClick={saveDraft}>
                    Save Draft
                  </button>
                  <button className="rounded bg-green-600 px-4 py-2 text-white" onClick={submitKYC}>
                    Submit
                  </button>
                </div>
              </div>
              {submission && (
                <div className="rounded bg-white p-4 shadow">
                  <p>Current state: <b>{submission.state}</b></p>
                  {submission.reviewer_reason && <p>Reviewer reason: {submission.reviewer_reason}</p>}
                </div>
              )}
            </div>
          ) : (
            <div className="grid gap-4 lg:grid-cols-3">
              <div className="rounded bg-white p-4 shadow lg:col-span-2">
                <div className="mb-3 flex items-center justify-between">
                  <h2 className="text-xl font-semibold">Reviewer Queue</h2>
                  <button className="rounded bg-indigo-600 px-3 py-2 text-white" onClick={loadQueue}>
                    Refresh
                  </button>
                </div>
                {metrics && (
                  <div className="mb-4 grid grid-cols-1 gap-2 md:grid-cols-3">
                    <div className="rounded bg-slate-100 p-2">In queue: {metrics.submissions_in_queue}</div>
                    <div className="rounded bg-slate-100 p-2">Avg queue sec: {Math.round(metrics.avg_time_in_queue_seconds)}</div>
                    <div className="rounded bg-slate-100 p-2">Approval 7d: {metrics.approval_rate_last_7_days}%</div>
                  </div>
                )}
                <div className="space-y-2">
                  {queue.map((item) => (
                    <div key={item.id} className="flex items-center justify-between rounded border p-3">
                      <div>
                        <p className="font-semibold">{item.business_name || item.personal_name || `Submission ${item.id}`}</p>
                        <p className="text-sm text-gray-600">State: {item.state} {item.at_risk ? "| At Risk >24h" : ""}</p>
                      </div>
                      <button className="rounded bg-slate-700 px-3 py-1 text-white" onClick={() => loadSubmissionDetail(item.id)}>
                        Open
                      </button>
                    </div>
                  ))}
                </div>
              </div>
              <div className="rounded bg-white p-4 shadow">
                <h3 className="mb-2 text-lg font-semibold">Submission Detail</h3>
                {!selectedSubmission ? (
                  <p className="text-sm text-gray-600">Select a queue item.</p>
                ) : (
                  <div className="space-y-2 text-sm">
                    <p>ID: {selectedSubmission.id}</p>
                    <p>State: {selectedSubmission.state}</p>
                    <p>Name: {selectedSubmission.personal_name}</p>
                    <p>Business: {selectedSubmission.business_name}</p>
                    <textarea className="mt-2 w-full rounded border p-2" rows={3} placeholder="Reason (required for reject/more info)" value={reviewReason} onChange={(e) => setReviewReason(e.target.value)} />
                    <div className="grid grid-cols-2 gap-2">
                      <button className="rounded bg-blue-600 px-2 py-1 text-white" onClick={() => takeAction("start_review")}>Start Review</button>
                      <button className="rounded bg-green-600 px-2 py-1 text-white" onClick={() => takeAction("approve")}>Approve</button>
                      <button className="rounded bg-red-600 px-2 py-1 text-white" onClick={() => takeAction("reject")}>Reject</button>
                      <button className="rounded bg-amber-600 px-2 py-1 text-white" onClick={() => takeAction("request_more_info")}>More Info</button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
