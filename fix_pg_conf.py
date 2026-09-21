path = '/etc/postgresql/16/main/postgresql.conf'
with open(path, 'r') as f:
    content = f.read()

new_content = content.replace("#listen_addresses = 'localhost'", "listen_addresses = '*'")
with open(path, 'w') as f:
    f.write(new_content)

print("POSTGRES_CONF_UPDATED_SUCCESSFULLY")
