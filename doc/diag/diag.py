from graphviz import Digraph

# Create a more compact top-down (vertical) diagram
dot = Digraph('architecture_diagram', format='png')
dot.attr(rankdir='TB')  # top-to-bottom layout
dot.attr('node', shape='box')

# Nodes
dot.node('U', 'Utilizator')
dot.node('API', 'Calendar API Service (Replicated)')
dot.node('Auth', 'Keycloak')
dot.node('Profile', 'User Profile Service')
dot.node('DB1', 'Calendar DB')
dot.node('DB2', 'User Profile DB')
dot.node('Redis', 'Redis (Distributed Locking)')
dot.node('MQ', 'RabbitMQ')
dot.node('W', 'Worker (Replicated Service)')


# Connections (more vertically arranged)
dot.edge('U', 'API', label='HTTP / JWT')
dot.edge('API', 'Auth', label='OAuth2 / OIDC')
dot.edge('Auth', 'Profile', label='User Metadata')
dot.edge('Profile', 'DB2', label='Store')
dot.edge('API', 'DB1', label='CRUD')
dot.edge('API', 'Redis', label='Distributed Locking')
dot.edge('API', 'MQ', label='Publish Job')

dot.edge('MQ', 'W')

dot.edge('W', 'DB1')
# Save
output_path = 'out/architecture_diagram'
dot.render(output_path, cleanup=True)

print("Generated:", output_path + '.png')
