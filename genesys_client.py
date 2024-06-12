import requests
import PureCloudPlatformClientV2
from PureCloudPlatformClientV2.rest import ApiException

client_id = 'ENTER CLIENT ID'
client_secret = 'Enter client secret'
region = 'mypurecloud.com.au'  # Correct region for Sydney, Australia

# Set up the Genesys Cloud API client
def get_api_client():
    token_url = f'https://login.{region}/oauth/token'
    auth_response = requests.post(token_url, data={
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    })
    auth_response.raise_for_status()
    access_token = auth_response.json().get('access_token')

    PureCloudPlatformClientV2.configuration.host = f'https://api.{region}'
    PureCloudPlatformClientV2.configuration.access_token = access_token
    users_api_instance = PureCloudPlatformClientV2.UsersApi()
    authorization_api_instance = PureCloudPlatformClientV2.AuthorizationApi()
    routing_api_instance = PureCloudPlatformClientV2.RoutingApi()
    telephony_providers_edge_api_instance = PureCloudPlatformClientV2.TelephonyProvidersEdgeApi()
    return users_api_instance, authorization_api_instance, routing_api_instance, telephony_providers_edge_api_instance

def get_all_users(users_api_instance):
    try:
        all_users = []
        page_number = 1
        while True:
            users = users_api_instance.get_users(page_size=100, page_number=page_number)
            all_users.extend(users.entities)
            if not users.next_uri:
                break
            page_number += 1
        print(f"Fetched {len(all_users)} users")
        for user in all_users:
            print(f"User: {user.id} - {user.name}")
        return all_users
    except ApiException as e:
        print("Exception when calling UsersApi->get_users: %s\n" % e)
        return []

def get_user_queues(users_api_instance, user_id):
    try:
        user_queues = users_api_instance.get_user_queues(user_id)
        print(f"Fetched {len(user_queues.entities)} queues for user {user_id}")
        return user_queues.entities
    except ApiException as e:
        if e.status == 404:
            print(f"No queues found for user {user_id}")
            return []
        else:
            print("Exception when calling UsersApi->get_user_queues: %s\n" % e)
            return []

def get_user_skills(users_api_instance, user_id):
    try:
        user_skills = users_api_instance.get_user_routingskills(user_id)
        print(f"Fetched {len(user_skills.entities)} skills for user {user_id}")
        return user_skills.entities
    except ApiException as e:
        if e.status == 404:
            print(f"No skills found for user {user_id}")
            return []
        else:
            print("Exception when calling UsersApi->get_user_routingskills: %s\n" % e)
            return []

def get_user_roles(authorization_api_instance, user_id):
    try:
        user_roles = authorization_api_instance.get_user_roles(user_id)
        print(f"Fetched {len(user_roles.roles)} roles for user {user_id}")
        for role in user_roles.roles:
            print(f"Role: {role.id} - {role.name}")
        return user_roles.roles
    except ApiException as e:
        if e.status == 404:
            print(f"No roles found for user {user_id}")
            return []
        else:
            print("Exception when calling AuthorizationApi->get_user_roles: %s\n" % e)
            return []

def add_user_to_queue(routing_api_instance, user_id, queue_id):
    try:
        body = PureCloudPlatformClientV2.UserQueue()
        body.id = user_id
        routing_api_instance.post_routing_queue_users(queue_id, [body])
        print(f"Added user {user_id} to queue {queue_id}")
    except ApiException as e:
        print(f"Exception when calling post_routing_queue_users: {e}\n")

def add_user_skill(users_api_instance, user_id, skill_id, proficiency):
    try:
        skill = PureCloudPlatformClientV2.UserRoutingSkillPost()
        skill.id = skill_id
        skill.proficiency = proficiency  # Set proficiency here
        print(f"Adding skill {skill_id} with proficiency {skill.proficiency} to user {user_id}")
        users_api_instance.patch_user_routingskills_bulk(user_id, [skill])
        print(f"Added skill {skill_id} to user {user_id}")
    except ApiException as e:
        print(f"Exception when calling patch_user_routingskills_bulk: {e}\n")

def add_user_role(authorization_api_instance, user_id, role_id):
    try:
        # Fetch the current roles of the user
        current_roles = authorization_api_instance.get_user_roles(user_id).roles
        current_role_ids = [role.id for role in current_roles]
        print(f"Current roles for user {user_id}: {current_role_ids}")

        # Add the new role to the list of current roles
        if role_id not in current_role_ids:
            current_role_ids.append(role_id)
            print(f"Adding role {role_id} to user {user_id}")

            # Update the user's roles
            authorization_api_instance.put_user_roles(user_id, current_role_ids)
            print(f"Added role {role_id} to user {user_id}")
        else:
            print(f"Role {role_id} already exists for user {user_id}")
    except ApiException as e:
        print(f"Exception when calling put_user_roles: {e}\n")

def create_phone(telephony_providers_edge_api_instance, user_id, phone_name, site_id):
    try:
        phone_base_id = "9de46512-77f0-49d3-b1fd-0aeb3e63764f"
        line_base_id = "5c431e9b-aff1-4668-89df-e1c487bd5a78"
        phone_body = {
            "name": phone_name,
            "site": {"id": site_id},
            "phoneBaseSettings": {"id": phone_base_id},
            "webRtcUser": {"id": user_id},
            "lines": [
                {"lineBaseSettings": {"id": line_base_id}}
            ]
        }
        api_response = telephony_providers_edge_api_instance.post_telephony_providers_edges_phones(phone_body)
        return api_response
    except ApiException as e:
        print(f"Exception when calling TelephonyProvidersEdgeApi->post_telephony_providers_edges_phones: {e}\n")
        raise

def get_user_details(users_api_instance, user_id):
    try:
        user_details = users_api_instance.get_user(user_id)
        return user_details
    except ApiException as e:
        print(f"Exception when calling UsersApi->get_user: %s\n" % e)
        return None

def get_user_phones(telephony_providers_edge_api_instance, user_id):
    try:
        user_phones = telephony_providers_edge_api_instance.get_telephony_providers_edges_phones(web_rtc_user_id=user_id)
        return user_phones.entities
    except ApiException as e:
        print(f"Exception when calling TelephonyProvidersEdgeApi->get_telephony_providers_edges_phones: %s\n" % e)
        return None
