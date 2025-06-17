param location string = resourceGroup().location
param containerName string = 'sandbox-container'
param storageAccountName string = toLower('sa${uniqueString(resourceGroup().id)}')
param registryName string
param containerImage string
param containerRegistryServer string
param containerRegistryUsername string
@secure()
param containerRegistryPassword string
param fileShareName string = 'projects'
param mountPath string = '/projects'
@secure()
param githubToken string

var queueServiceName = 'default'
var commandQueue = 'commandqueue'
var responseQueue = 'responsequeue'

resource storageAccount 'Microsoft.Storage/storageAccounts@2021-08-01' = {
  name: storageAccountName
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    supportsHttpsTrafficOnly: true
  }
}

resource fileShare 'Microsoft.Storage/storageAccounts/fileServices/shares@2021-08-01' = {
  name: '${storageAccount.name}/default/${fileShareName}'
  dependsOn: [storageAccount]
}

resource commandQueueRes 'Microsoft.Storage/storageAccounts/queueServices/queues@2021-08-01' = {
  name: '${storageAccount.name}/${queueServiceName}/${commandQueue}'
  dependsOn: [storageAccount]
}

resource responseQueueRes 'Microsoft.Storage/storageAccounts/queueServices/queues@2021-08-01' = {
  name: '${storageAccount.name}/${queueServiceName}/${responseQueue}'
  dependsOn: [storageAccount]
}

resource containerGroup 'Microsoft.ContainerInstance/containerGroups@2021-09-01' = {
  name: containerName
  location: location
  dependsOn: [fileShare, commandQueueRes, responseQueueRes]
  properties: {
    osType: 'Linux'
    restartPolicy: 'OnFailure'
    ipAddress: {
      type: 'Public'
      ports: [
        {
          protocol: 'TCP'
          port: 3000
        }
      ]
    }
    imageRegistryCredentials: [
      {
        server: containerRegistryServer
        username: containerRegistryUsername
        password: containerRegistryPassword
      }
    ]
    containers: [
      {
        name: containerName
        properties: {
          image: containerImage
          resources: {
            requests: {
              cpu: 1
              memoryInGB: 1.5
            }
          }
          ports: [
            {
              port: 3000
            }
          ]
          volumeMounts: [
            {
              name: 'projects-volume'
              mountPath: mountPath
              readOnly: false
            }
          ]
          environmentVariables: [
            {
              name: 'AZURE_STORAGE_CONNECTION_STRING'
              secureValue: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${listKeys(storageAccount.id, storageAccount.apiVersion).keys[0].value};EndpointSuffix=${environment().suffixes.storage}'
            }
            {
              name: 'COMMAND_QUEUE'
              value: commandQueue
            }
            {
              name: 'RESPONSE_QUEUE'
              value: responseQueue
            }
            {
              name: 'GITHUB_TOKEN'
              secureValue: githubToken
            }
          ]
        }
      }
    ]
    volumes: [
      {
        name: 'projects-volume'
        azureFile: {
          shareName: fileShareName
          storageAccountName: storageAccount.name
          storageAccountKey: listKeys(storageAccount.id, storageAccount.apiVersion).keys[0].value
        }
      }
    ]
  }
}

output containerIPv4Address string = containerGroup.properties.ipAddress.ip
output storageAccountName string = storageAccount.name
output storageConnectionString string = 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${listKeys(storageAccount.id, storageAccount.apiVersion).keys[0].value};EndpointSuffix=${environment().suffixes.storage}'
output commandQueueName string = commandQueue
output responseQueueName string = responseQueue
