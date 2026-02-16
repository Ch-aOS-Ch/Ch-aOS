def handleExplain(args):
    from chaos.lib.explain import handleExplain

    if args.topics:
        from chaos.lib.args.dataclasses import ExplainPayload
        from chaos.lib.plugDiscovery import get_plugins

        payload = ExplainPayload(
            topics=args.topics,
            complexity=args.complexity,
            details=args.details,
            no_pretty=args.no_pretty,
            json=args.json,
        )

        EXPLANATIONS = get_plugins(args.update_plugins)[2]
        handleExplain(payload, EXPLANATIONS)
    else:
        print("No explanation passed.")
