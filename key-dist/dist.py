from globus_compute_sdk import Executor
import paramiko



guys = {
    "this": ["server.crt"],
    "that": ["server.key", "server.crt"],
    "neat": ["server.key", "server.crt"],
    "swell": ["server.crt"]
}


"""
def dist_keys(guy, keys):
    for key in keys:
        try:
            subprocess.run(
                ["scp", key, f"{guy}:./"],
                check=True
            )
            print(f"sent to {guy}")
        except subprocess.CalledProcessError as e:
            print(f"didn't sent to {guy}: {e}")

"""




def dist_keys(guy, files):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_config_file = paramiko.config.SSHConfig()
        with open("/home/seena/.ssh/config") as f:
            ssh_config_file.parse(f)

        host_config = ssh_config_file.lookup(guy)
        hostname = host_config.get("hostname", guy)
        user = host_config.get("user")
        keyfile = host_config.get("identityfile", [None])[0]

        ssh.connect(
            hostname,
            username=user,
            key_filename=keyfile,
            look_for_keys=True,
            timeout=10
        )

        sftp = ssh.open_sftp()
        for file in files:
            sftp.put(file, f"/{file}")
        sftp.close()
        print(f"sent to {guy}")
    except Exception as e:
        print(f"didn't sent to {guy}: {e}")
    finally:
        ssh.close()

for guy, files in guys.items():
    dist_keys(guy, files)