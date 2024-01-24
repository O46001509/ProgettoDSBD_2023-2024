# ProgettoDSBD_2023-2024

Progetto Elaborato del corso di DISTRIBUTED SYSTEMS AND BIG DATA.

## Tabella dei Contenuti

- [Descrizione](#descrizione)
- [Installazione](#installazione)
- [Utilizzo](#utilizzo)
- [Autori](#autori)

## Descrizione

Il progetto è suddiviso in: prima-parte e seconda-parte.

```mermaid
graph TB
    subgraph services
        style services fill:#fff,stroke:#000,stroke-width:2px,stroke-dasharray:5
        subgraph cluster_postgres
            style cluster_postgres yellow fill:#fff,stroke:#000,stroke-width:2px,stroke-dasharray:5
            DB
            B[database-service] --> |5432| A[(postgresSQL)]
        end

        subgraph cluster_weather_event_notifier
            style cluster_weather_event_notifier yellow fill:#fff,stroke:#000,stroke-width:2px,stroke-dasharray:5
            C["Weather Event Notifier"] <-->|API:5004 handle persistent subscriptions \nand users| B[database-service]
        end

        subgraph cluster_weather_data_fetcher
            style cluster_weather_data_fetcher yellow fill:#fff,stroke:#000,stroke-width:2px,stroke-dasharray:5
            E["Weather Data Fetcher"] 
        end

        subgraph cluster_notification_service
            style cluster_notification_service yellow fill:#fff,stroke:#000,stroke-width:2px,stroke-dasharray:5
            D["Notification Service"]
        end
    end

    subgraph cluster_sla_manager_service
        M[SLA Manager] -->|metrics to monitor| H
        M <-->|API:5004 handle \npersistent metrics' state| B
    end

    H["prometheus (monitoring)"] --> |API - monitoring| services
    H -->|Visualization| grafana
    D --> |API: Send-notification \nto user| I((bot Telegram)) 
    I --> |Sending a new\nregistration| L[handle-users-service]
    L --> |API:5004/Insert new user| B
    E <-->|get_info_meteo_bycity| N[CLASS: OpenWeatherWrapper] -->|API: get_weather_bycity| O((OpenWeatherMap))
    C -->|new subscription: user_name, city| E
    E -->|send notification \nby new subscription| D 

    style A fill:#fff,stroke:#000,stroke-width:2px,stroke-dasharray:5

    user1((utente)) -->|/start sign-up| I
    I --> |Send-notification| user1 -->|API:5001/subscriptions?username&city&conditions| C

    style user1 fill:#0f0,stroke-width:2px,stroke-dasharray:0
    style I fill:#f09,stroke-width:0px
    style O fill:#f09,stroke-width:0px
```

## Installazione

Passaggi necessari per l'installazione e la configurazione del progetto.

```bash
# Esempio di comando di installazione
docker-compose up
```

## Utilizzo

...

## Autori

Giovanni Domenico Tassi, Oleksandr Merlino Lenko
