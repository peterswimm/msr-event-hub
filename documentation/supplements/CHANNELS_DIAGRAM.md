# Channels Overview (Publishable)

```text
                 +-------------------------------------+
                 |          Core Extraction             |
                 |   Paper / Talk / Repo                |
                 |   Structured JSON + summaries        |
                 +-------------------------------------+
                     /           |             |            \
                    /            |             |             \
            +-----------+  +---------------+  +------------------+  +--------------------+
            | Local CLI |  | Microsoft 365 |  | Azure AI Foundry |  |  Power Platform    |
            |   (T1)    |  |    (T2)       |  |      (T3)        |  |       (T4)         |
            | outputs/  |  | SP/OD + Teams |  | Managed models   |  | Automate / Apps / BI|
            | fast loop |  | governed store|  | Eval / monitoring|  | REST API surface    |
            +-----------+  +---------------+  +------------------+  +--------------------+

Cross-cutting
- Unified settings (extended_settings.py)
- Pipeline orchestration (core_interfaces.py)
- Adapters (M365 sources/sinks/notifier; Foundry provider)
```

- Use this ASCII diagram in docs or slides to show where the agent runs and how channels connect.
- Edit the block as needed for additional channels or surfaces.
