from flask import Flask, redirect, url_for, session, request, jsonify, render_template
from requests_oauthlib import OAuth2Session
from genesys_client import (
    get_api_client, get_all_users, get_user_queues, get_user_skills, get_user_roles,
    add_user_to_queue, add_user_skill, add_user_role, create_phone, get_user_details, get_user_phones
)
import logging
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, AUTHORIZATION_BASE_URL, TOKEN_URL

app = Flask(__name__)
app.secret_key = 'random_secret_key'  # Replace with a real secret key

@app.route('/')
def index():
    if 'oauth_token' in session:
        return render_template('index.html')
    return redirect(url_for('login'))

@app.route('/login')
def login():
    genesys = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI)
    authorization_url, state = genesys.authorization_url(AUTHORIZATION_BASE_URL)

    # State is used to prevent CSRF, keep this for later.
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route('/callback', methods=['GET'])
def callback():
    genesys = OAuth2Session(CLIENT_ID, state=session['oauth_state'], redirect_uri=REDIRECT_URI)
    token = genesys.fetch_token(TOKEN_URL, client_secret=CLIENT_SECRET, authorization_response=request.url)

    # Save the token in the session
    session['oauth_token'] = token

    return redirect(url_for('index'))

@app.before_request
def before_request():
    if 'oauth_token' not in session and request.endpoint not in ('login', 'callback'):
        return redirect(url_for('login'))

@app.route('/get_users', methods=['GET'])
def fetch_users():
    users = get_all_users(users_api_instance)
    user_list = [{'id': user.id, 'name': user.name} for user in users]
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
            results.append({
                'id': user.id,
                'name': user.name,
                'queues': [q.name for q in queues],
                'skills': [s.name for s in skills],
                'roles': [r.name for r in roles]
            })
            if selected_user_id and user.id == selected_user_id:
                break
    
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
        if copy_queues:
            queues = get_user_queues(users_api_instance, from_user_id)
            for queue in queues:
                add_user_to_queue(routing_api_instance, to_user_id, queue.id)

        if copy_skills:
            skills = get_user_skills(users_api_instance, from_user_id)
            for skill in skills:
                add_user_skill(users_api_instance, to_user_id, skill.id)

        if copy_roles:
            roles = get_user_roles(authorization_api_instance, from_user_id)
            for role in roles:
                add_user_role(authorization_api_instance, to_user_id, role.id)

        if copy_phone:
            to_user_details = get_user_details(users_api_instance, to_user_id)
            if not to_user_details:
                return jsonify({'status': 'error', 'message': 'To user details not found'}), 500

            to_user_name = f"PC - {to_user_details.name}"
            from_user_phones = get_user_phones(telephony_providers_edge_api_instance, from_user_id)
            if not from_user_phones:
                return jsonify({'status': 'error', 'message': 'No phone found for from user'}), 500

            site_id = from_user_phones[0].site.id
            phone_response = create_phone(
                telephony_providers_edge_api_instance,
                to_user_id,
                to_user_name,
                site_id
            )
        
        return jsonify({'status': 'success'})
    except Exception as e:
        logging.error(f"Error during copying details: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
