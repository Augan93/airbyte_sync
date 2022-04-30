# ensure we have correct structure for configuration
mkdir work_files
mkdir work_files/config
mkdir -p work_files/config/sources/github_custom
mkdir -p work_files/config/destinations/bigquery
mkdir -p work_files/config/connections/github_to_bigquery

# TODO: install jq and yq

# Configure octavia
echo "OCTAVIA_ENABLE_TELEMETRY=False" > ~/.octavia
octavia=''

# First, we need to get the id of source definition
if [ ! -f ./work_files/source_definition_id ]
then
    echo "Creating github_custom source definition"
    curl -d '{ "name": "github_custom", "dockerRepository": "dkishylau/source-github", "dockerImageTag": "0.2.29", "documentationUrl": "http://example.com"}' \
        -H 'Content-Type: application/json' \
        -X POST \
        http://localhost:8000/api/v1/source_definitions/create > ./work_files/create_source_definition.json
    cat ./work_files/create_source_definition.json | jq '.sourceDefinitionId' > ./work_files/source_definition_id
else
    echo "Using existing github_custom source definition"
fi

export SOURCE_DEFINITION_ID=$(cat ./work_files/source_definition_id)

# Generate source and destination configs
cat templates/source.yaml.templ | envsubst '$SOURCE_DEFINITION_ID' > ./work_files/config/sources/github_custom/configuration.yaml
cat templates/destination.yaml.templ > ./work_files/config/destinations/bigquery/configuration.yaml

echo 'Running Octavia'
# Now we need to run octavia and create/update source and destination
docker run -i --rm -v $(pwd)/work_files/config:/home/octavia-project --network host --env-file ~/.octavia --user $(id -u):$(id -g) airbyte/octavia-cli:0.36.4-alpha apply --force --file ./sources/github_custom/configuration.yaml
docker run -i --rm -v $(pwd)/work_files/config:/home/octavia-project --network host --env-file ~/.octavia --user $(id -u):$(id -g) airbyte/octavia-cli:0.36.4-alpha apply --force --file ./destinations/bigquery/configuration.yaml

# Extract source and destination identifiers so that we can use them in the connection file
export SOURCE_ID=$(cat ./work_files/config/sources/github_custom/state.yaml | yq ".resource_id")
export DESTINATION_ID=$(cat ./work_files/config/destinations/bigquery/state.yaml | yq ".resource_id")

# We also need to create an operation for connection
# First, get workspace id
export WORKSPACE_ID=$(curl -H 'Content-Type: application/json' -X POST http://localhost:8000/api/v1/workspaces/list | jq ".workspaces[0].workspaceId")

# Create an operation
if [ ! -f ./work_files/operation_id ]
then
    echo "Creating normalization operation"
    curl -d '{ "workspaceId": '${WORKSPACE_ID}', "name": "Normalization", "operatorConfiguration": {"operatorType": "normalization", "normalization": { "option": "basic"},"dbt": null}}' \
    -H 'Content-Type: application/json' -X POST http://localhost:8000/api/v1/operations/create > ./work_files/operation_create.json
    cat ./work_files/operation_create.json | jq ".operationId" > ./work_files/operation_id
else
    echo "Using existing operation id"
fi

export OPERATION_ID=$(cat ./work_files/operation_id)

cat templates/connection.yaml.templ | envsubst '$SOURCE_ID $DESTINATION_ID $OPERATION_ID' > ./work_files/config/connections/github_to_bigquery/configuration.yaml
docker run -i --rm -v $(pwd)/work_files/config:/home/octavia-project --network host --env-file ~/.octavia --user $(id -u):$(id -g) airbyte/octavia-cli:0.36.4-alpha apply --force --file ./connections/github_to_bigquery/configuration.yaml
# Save connection id in a file, so that we can use it
cat ./work_files/config/connections/github_to_bigquery/state.yaml | yq ".resource_id" > ./work_files/connection_id
