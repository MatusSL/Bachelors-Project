import { supabase } from "./supabase";

const API_BASE = import.meta.env.VITE_API_URL;

async function authHeaders() {
  const { data: { session } } = await supabase.auth.getSession();
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${session?.access_token}`,
  };
}

async function throwIfError(response) {
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.detail || `API error: ${response.status}`);
  }
}

export async function sendMessage(sessionId, message) {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: await authHeaders(),
    body: JSON.stringify({ session_id: sessionId, message }),
  });

  await throwIfError(response);
  return response.json();
}

export async function createSession() {
  const response = await fetch(`${API_BASE}/sessions`, {
    method: 'POST',
    headers: await authHeaders(),
  });

  await throwIfError(response);
  return response.json();
}

export async function getSessions() {
  const response = await fetch(`${API_BASE}/sessions`, {
    method: 'GET',
    headers: await authHeaders(),
  });

  await throwIfError(response);

  return response.json();
}

export async function getSession(sessionId) {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}`, {
    method: 'GET',
    headers: await authHeaders(),
  });

  await throwIfError(response);
  return response.json();
}

export async function exportChecklist(sessionId) {
  const { data: { session } } = await supabase.auth.getSession();
  const response = await fetch(`${API_BASE}/sessions/${sessionId}/export`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${session?.access_token}`,
    },
  });

  await throwIfError(response);

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `checklist-${sessionId}.xlsx`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export async function deleteSession(sessionId) {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}`, {
    method: 'DELETE',
    headers: await authHeaders(),
  });

  await throwIfError(response);

  if (response.status !== 204) {
    return response.json();
  }
}
