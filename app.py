from flask import Flask, request, jsonify
import pymongo
import requests
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.neighbors import NearestNeighbors
app = Flask(__name__)
MONGO_URI = "mongodb+srv://theprithivraj:h1h2h3h4@prithiv.xaz8u.mongodb.net/?retryWrites=true&w=majority&appName=prithiv"
client = pymongo.MongoClient(MONGO_URI)
db = client['LinkUpDB']
collection = db['users']
API_KEY = "c0ef56ccca986fa61939b6ef12edfd14"  
@app.before_first_request
def before_first_request():
    try:
        client.server_info() 
    except pymongo.errors.ServerSelectionTimeoutError as e:
        return jsonify({"message": "Database connection failed", "error": str(e)}), 500
@app.route('/warmup', methods=['GET'])
def warmup():
    try:
        client.server_info() 
        return jsonify({"message": "App is warmed up and ready!"})
    except pymongo.errors.ServerSelectionTimeoutError as e:
        return jsonify({"message": "Database connection failed", "error": str(e)}), 500
@app.route('/predict2', methods=['GET'])
def predict2():
    return "Hi, this is a test route!"
@app.route('/upload_image', methods=['POST'])
def upload_image():
    try:
        if 'image' not in request.files:
            return jsonify({'message': 'No image file found in the request.'}), 400
        file = request.files['image']
        if file.filename == '':
            return jsonify({'message': 'No selected file.'}), 400
        if file:
            image_url = upload_to_imgbb(file)
            return jsonify({'message': 'Image uploaded successfully', 'image_url': image_url})
    except Exception as e:
        return jsonify({'message': 'An error occurred', 'error': str(e)}), 500
def upload_to_imgbb(image_file):
    """Uploads the image file to ImgBB and returns the URL."""
    url = 'https://api.imgbb.com/1/upload'
    files = {'image': image_file}
    params = {'key': API_KEY}
    response = requests.post(url, files=files, data=params)
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            return result['data']['url'] 
        else:
            raise Exception(f"Error: {result['error']['message']}")
    else:
        raise Exception(f"Failed to upload image. Status Code: {response.status_code}")
@app.route('/predict', methods=['POST'])
def predict():
    try:
        user_data = request.json
        if not user_data or 'interests' not in user_data:
            return jsonify({'message': 'Invalid input. "interests" field is required.'}), 400
        user_interests = user_data.get('interests', [])
        if not isinstance(user_interests, list):
            return jsonify({'message': '"interests" must be a list of interests.'}), 400
        users = list(collection.find({}, {"_id": 1, "name": 1, "interests": 1, "profilePic": 1}))

        if not users:
            return jsonify({'message': 'No users available for matching'}), 400
        user_interests_data = [user['interests'] for user in users if 'interests' in user]
        
        mlb = MultiLabelBinarizer()
        X = mlb.fit_transform(user_interests_data)
        n_neighbors = min(len(users), 10)
        model = NearestNeighbors(n_neighbors=n_neighbors)
        model.fit(X)
        user_encoded = mlb.transform([user_interests])
        distances, indices = model.kneighbors(user_encoded, n_neighbors=n_neighbors)
        matched_users = []
        for idx in indices[0]:
            matched_users.append({
                'id': str(users[idx]['_id']),
                'name': users[idx]['name'],
                'interests': users[idx]['interests'],
                'profile_pic': users[idx].get('profilePic', '/default-avatar.jpg')
            })
        return jsonify({
            'message': 'Matching users found',
            'matched_users': matched_users
        })
    except pymongo.errors.PyMongoError as e:
        return jsonify({'message': 'Database error', 'error': str(e)}), 500
    except Exception as e:
        return jsonify({'message': 'An error occurred', 'error': str(e)}), 500
@app.errorhandler(Exception)
def handle_error(error):
    return jsonify({"message": "An error occurred", "error": str(error)}), 500
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
