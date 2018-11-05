     _   _                _                    _   
    | | | | __ ___      _| | ___ __   ___  ___| |_ 
    | |_| |/ _` \ \ /\ / / |/ / '_ \ / _ \/ __| __|
    |  _  | (_| |\ V  V /|   <| | | |  __/\__ \ |_ 
    |_| |_|\__,_| \_/\_/ |_|\_\_| |_|\___||___/\__|
                                                    

# The Intelligent Content Management Platform

Built to store files and metadata and retrieve in a smart way

If using docker-compose, set the following environment variables in a file called secrets.env at root of this repo:

| VARIABLE                   | DESCRIPTION                                           |
|----------------------------|-------------------------------------------------------|
| MONGO_HOST                 | The host of MongoDB.                                  |
| MONGO_DBNAME               | The name of MongoDB database.                         |
| LDAP_HOST                  | The host name or IP address of your LDAP server.      |
| LDAP_USERNAME              | The user name used to bind.                           |
| LDAP_PASSWORD              | The password used to bind.                            |
| LDAP_BASE_DN               | The distinguished name to use as the search base.     |
| LDAP_DOMAIN                | The domain of LDAP server.                            |
| APP_NAME                   | The name of the application, to show for final users. |
| ADMIN_USERS                | The system administrators, separated by comma (,).    |
| ELASTICSEARCH_URI          | The URI for the elasticsearch server                  |
| ELASTICSEARCH_INDEX        | The name of the elasticsearch index on the server     |