#Creation with phone
from flask import Flask, request, jsonify, render_template
from genesys_client import (
    get_api_client, get_users, get_user_queues, get_user_skills, get_user_roles,
    add_user_to_queue, add_user_skill, add_user_role, create_phone, get_user_details
)
import logging

app = Flask(__name__)
(users_api_instance, authorization_api_instance, routing_api_instance, 
 telephony_providers_edge_api_instance) = get_api_client()

# Set up logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_users', methods=['GET'])
def fetch_users():
    users = get_users(users_api_instance)
    user_list = [{'id': user.id, 'name': user.name} for user in users]
    print(f"User list: {user_list}")
    return jsonify(user_list)

@app.route('/search', methods=['POST'])
def search_users():
    search_text = request.form['search_text']
    selected_user_id = request.form.get('selected_user_id')
    users = get_users(users_api_instance)
    results = []
    
    for user in users:
        if search_text.lower() in user.name.lower() or search_text.lower() in user.email.lower() or (selected_user_id and user.id == selected_user_id):
            queues = get_user_queues(users_api_instance, user.id)
            skills = get_user_skills(users_api_instance, user.id)
            roles = get_user_roles(authorization_api_instance, user.id)
            print(f"User: {user.name}, Queues: {queues}, Skills: {skills}, Roles: {roles}")  # Debugging line
            results.append({
                'id': user.id,
                'name': user.name,
                'queues': [q.name for q in queues],
                'skills': [s.name for s in skills],
                'roles': [r.name for r in roles]
            })
            # If searching by selected user ID, break after finding the user
            if selected_user_id and user.id == selected_user_id:
                break
    
    print(f"Search results: {results}")  # Debugging line
    return jsonify(results)

@app.route('/copy', methods=['POST'])
def copy_details():
    from_user_id = request.form['from_user_id']
    to_user_id = request.form['to_user_id']
    
    try:
        # Copy queues
        queues = get_user_queues(users_api_instance, from_user_id)
        for queue in queues:
            print(f"Adding queue {queue.id} to user {to_user_id}")
            add_user_to_queue(routing_api_instance, to_user_id, queue.id)

        # Copy skills
        skills = get_user_skills(users_api_instance, from_user_id)
        for skill in skills:
            print(f"Adding skill {skill.id} to user {to_user_id}")
            add_user_skill(users_api_instance, to_user_id, skill.id)

        # Copy roles
        roles = get_user_roles(authorization_api_instance, from_user_id)
        for role in roles:
            print(f"Adding role {role.id} to user {to_user_id}")
            add_user_role(authorization_api_instance, to_user_id, role.id)

        # Get user details
        to_user_details = get_user_details(users_api_instance, to_user_id)
        if not to_user_details:
            return jsonify({'status': 'error', 'message': 'To user details not found'}), 500

        to_user_name = f"PC - {to_user_details.name}"

        # Create phone
        phone_response = create_phone(
            telephony_providers_edge_api_instance,
            to_user_id,
            to_user_name,
            "77a1e9c3-5466-422d-9af0-e22ab1ff16c0"
        )
        print(f"Created phone for user {to_user_id} with response: {phone_response}")

        return jsonify({'status': 'success'})
    except Exception as e:
        logging.error(f"Error during copying details: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
