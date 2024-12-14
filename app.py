from flask import Flask, request, jsonify
import pymongo
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.neighbors import NearestNeighbors

app = Flask(__name__)

MONGO_URI = "mongodb+srv://theprithivraj:h1h2h3h4@prithiv.xaz8u.mongodb.net/?retryWrites=true&w=majority&appName=prithiv"
client = pymongo.MongoClient(MONGO_URI)
db = client['LinkUpDB']
collection = db['users']

@app.route('/predict2', methods=['GET'])
def predict2():
    return "Hi, this is a test route!"

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
        
        user_data = [user['interests'] for user in users if 'interests' in user]
        if not user_data:
            return jsonify({'message': 'No users available for matching'}), 400
        mlb = MultiLabelBinarizer()
        X = mlb.fit_transform(user_data)
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
    except Exception as e:
        app.logger.error(f"Error occurred: {e}")
        return jsonify({'message': 'An error occurred', 'error': str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True, port=5000)
