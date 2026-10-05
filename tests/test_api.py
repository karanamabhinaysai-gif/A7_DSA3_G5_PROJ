import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_route(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"SRPS" in response.data or b"Recommendation" in response.data


def test_api_recommend(client):
    response = client.post(
        "/api/recommend",
        json={"query": "machine learning classification", "top_k": 5, "algorithm": "hybrid"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "results" in data
    assert len(data["results"]) > 0
    assert "title" in data["results"][0]
    assert "url" in data["results"][0]
    assert data["results"][0]["url"].startswith("http")
    assert "scholar_url" in data["results"][0]


def test_api_recommend_bm25(client):
    response = client.post(
        "/api/recommend",
        json={"query": "transformer attention", "top_k": 3, "algorithm": "bm25"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["results"]) > 0


def test_api_recommend_rrf(client):
    response = client.post(
        "/api/recommend",
        json={"query": "deep learning neural network", "top_k": 3, "algorithm": "rrf"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["results"]) > 0


def test_api_recommend_mmr(client):
    response = client.post(
        "/api/recommend",
        json={"query": "computer vision", "top_k": 3, "algorithm": "mmr"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["results"]) > 0


def test_api_graph_data(client):
    response = client.get("/api/graph/data")
    assert response.status_code == 200
    data = response.get_json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) > 0
    assert len(data["edges"]) > 0


def test_api_graph_analytics(client):
    response = client.get("/api/graph/analytics")
    assert response.status_code == 200
    data = response.get_json()
    assert "total_nodes" in data
    assert "density" in data
    assert "top_authorities" in data


def test_api_bookmarks_flow(client):
    # Add bookmark
    add_resp = client.post(
        "/api/bookmarks",
        json={"user_id": 1, "paper_id": 2, "status": "to_read", "notes": "Important reference"},
    )
    assert add_resp.status_code == 200
    assert add_resp.get_json()["success"] is True

    # Get bookmarks
    get_resp = client.get("/api/bookmarks?user_id=1")
    assert get_resp.status_code == 200
    b_data = get_resp.get_json()
    assert any(b["paper_id"] == 2 for b in b_data["bookmarks"])

    # Remove bookmark
    del_resp = client.delete("/api/bookmarks/2?user_id=1")
    assert del_resp.status_code == 200
    assert del_resp.get_json()["success"] is True


def test_api_export_bibtex(client):
    response = client.get("/api/export/bibtex?paper_id=1")
    assert response.status_code == 200
    assert b"@article" in response.data


def test_login_page_route(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Sign In" in response.data
    assert b"Create Account" in response.data


def test_api_login_success(client):
    response = client.post("/api/login", json={"username": "alice", "password": "alice123"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["username"] == "alice"
    assert data["user_id"] == 1


def test_api_login_invalid(client):
    response = client.post("/api/login", json={"username": "alice", "password": "wrongpassword"})
    assert response.status_code == 401
    assert "error" in response.get_json()


def test_api_register_and_profile(client):
    import uuid
    random_user = f"user_{uuid.uuid4().hex[:6]}"
    response = client.post(
        "/api/register",
        json={"username": random_user, "password": "securepass123", "interests": "robotics, RL"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    user_id = data["user_id"]

    # Verify profile
    prof_resp = client.get(f"/api/user/{user_id}")
    assert prof_resp.status_code == 200
    p_data = prof_resp.get_json()
    assert p_data["username"] == random_user
    assert "robotics" in p_data["interests"]


def test_api_evaluate(client):
    response = client.get("/api/evaluate?k=5")
    assert response.status_code == 200
    data = response.get_json()
    assert "models" in data
    assert "hybrid" in data["models"]
    assert "ndcg_at_k" in data["models"]["hybrid"]


def test_api_analyze_paper(client):
    response = client.post(
        "/api/analyze/paper",
        json={"text": "A deep residual neural network architecture for image recognition and classification benchmarks."},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "primary_domain" in data
    assert "recommended_foundational_citations" in data


def test_api_bibliometrics(client):
    response = client.get("/api/bibliometrics")
    assert response.status_code == 200
    data = response.get_json()
    assert "cocitation_pairs" in data
    assert "bibliographic_coupling" in data
    assert "top_influential_papers" in data


