(() => {
  const DEFAULT_API_BASE_URL = "http://localhost:8000";
  const TOKEN_KEY = "postais_admin_token";

  function getApiBaseUrl() {
    return (
      window.POSTAIS_API_BASE_URL ||
      localStorage.getItem("postais_api_base_url") ||
      DEFAULT_API_BASE_URL
    ).replace(/\/$/, "");
  }

  function setApiBaseUrl(url) {
    localStorage.setItem("postais_api_base_url", url.replace(/\/$/, ""));
  }

  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
  }

  function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
  }

  function buildUrl(path, params = {}) {
    const url = new URL(`${getApiBaseUrl()}${path}`);

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, value);
      }
    });

    return url.toString();
  }

  async function request(path, options = {}) {
    const headers = new Headers(options.headers || {});
    const token = getToken();

    if (options.body && !(options.body instanceof FormData)) {
      headers.set("Content-Type", "application/json");
    }

    if (options.auth !== false && token) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    const response = await fetch(buildUrl(path, options.params), {
      ...options,
      headers,
      body:
        options.body && !(options.body instanceof FormData)
          ? JSON.stringify(options.body)
          : options.body,
    });

    if (response.status === 204) {
      return null;
    }

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      const message = data?.detail || "Erro ao comunicar com a API.";
      throw new Error(message);
    }

    return data;
  }

  async function listarPostais({ page = 1, size = 12 } = {}) {
    return request("/postais", { auth: false, params: { page, size } });
  }

  async function listarPosts({ page = 1, size = 10, categoria } = {}) {
    return request("/posts", {
      auth: false,
      params: { page, size, categoria },
    });
  }

  async function listarCronicas(options = {}) {
    return listarPosts({ ...options, categoria: "cronica" });
  }

  async function loginAdmin(username, password) {
    const data = await request("/auth/login", {
      method: "POST",
      auth: false,
      body: { username, password },
    });

    setToken(data.access_token);
    return data;
  }

  async function criarPostal(postal) {
    return request("/postais", { method: "POST", body: postal });
  }

  async function editarPostal(id, postal) {
    return request(`/postais/${id}`, { method: "PUT", body: postal });
  }

  async function deletarPostal(id) {
    return request(`/postais/${id}`, { method: "DELETE" });
  }

  async function criarPost(post) {
    return request("/posts", { method: "POST", body: post });
  }

  async function editarPost(id, post) {
    return request(`/posts/${id}`, { method: "PUT", body: post });
  }

  async function deletarPost(id) {
    return request(`/posts/${id}`, { method: "DELETE" });
  }

  window.PostaisAPI = {
    clearToken,
    criarPost,
    criarPostal,
    deletarPost,
    deletarPostal,
    editarPost,
    editarPostal,
    getApiBaseUrl,
    getToken,
    listarCronicas,
    listarPostais,
    listarPosts,
    loginAdmin,
    setApiBaseUrl,
  };
})();
