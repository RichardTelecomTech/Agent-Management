from flask import Flask, request, jsonify, render_template
from genesys_client import (
    get_api_client, get_all_users, get_user_queues, get_user_skills, get_user_roles,
    add_user_to_queue, add_user_skill, add_user_role, create_phone, get_user_details, get_user_phones
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
    users = get_all_users(users_api_instance)
    user_list = [{'id': user.id, 'name': user.name} for user in users]
    print(f"User list: {user_list}")
    return jsonify(user_list)

@app.route('/search', methods=['POST'])
def search_users():
    search_text = request.form['search_text']
    selected_user_id = request.form.get('selected_user_id')
    users = get_all_users(users_api_instance)
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
    copy_queues = request.form.get('copy_queues') == '1'
    copy_skills = request.form.get('copy_skills') == '1'
    copy_roles = request.form.get('copy_roles') == '1'
    copy_phone = request.form.get('copy_phone') == '1'
    
    try:
        copy_messages = []
        
        if copy_queues:
            # Copy queues
            queues = get_user_queues(users_api_instance, from_user_id)
            for queue in queues:
                print(f"Adding queue {queue.id} to user {to_user_id}")
                add_user_to_queue(routing_api_instance, to_user_id, queue.id)
            copy_messages.append('queues')

        if copy_skills:
            # Copy skills
            skills = get_user_skills(users_api_instance, from_user_id)
            skill_posts = [PureCloudPlatformClientV2.UserRoutingSkillPost(routing_skill_id=skill.id, proficiency=1.0) for skill in skills]
            add_user_skill(users_api_instance, to_user_id, skill_posts)
            copy_messages.append('skills')

        if copy_roles:
            # Copy roles
            roles = get_user_roles(authorization_api_instance, from_user_id)
            for role in roles:
                print(f"Adding role {role.id} to user {to_user_id}")
                add_user_role(authorization_api_instance, to_user_id, role.id)
            copy_messages.append('roles')

        if copy_phone:
            # Get user details
            to_user_details = get_user_details(users_api_instance, to_user_id)
            if not to_user_details:
                return jsonify({'status': 'error', 'message': 'To user details not found'}), 500

            to_user_name = f"PC - {to_user_details.name}"

            # Get the site ID from the from_user_id
            from_user_phones = get_user_phones(telephony_providers_edge_api_instance, from_user_id)
            if not from_user_phones:
                return jsonify({'status': 'error', 'message': 'No phone found for from user'}), 500

            site_id = from_user_phones[0].site.id

            # Create phone
            phone_response = create_phone(
                telephony_providers_edge_api_instance,
                to_user_id,
                to_user_name,
                site_id
            )
            copy_messages.append(f'Phone created: {to_user_name}')
            print(f"Created phone for user {to_user_id} with response: {phone_response}")

        success_message = 'Details copied successfully for ' + ', '.join(copy_messages) + '!'
        return jsonify({'status': 'success', 'message': success_message})
    except Exception as e:
        logging.error(f"Error during copying details: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
