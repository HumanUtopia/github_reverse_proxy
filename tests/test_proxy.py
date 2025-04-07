import requests

def test_proxy():
    url = "http://localhost:5000/somepath"
    response = requests.get(url)
    assert response.status_code == 200
    print("Proxy server is working correctly")

if __name__ == '__main__':
    test_proxy()