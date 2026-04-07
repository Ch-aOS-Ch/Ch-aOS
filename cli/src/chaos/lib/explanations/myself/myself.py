class ExplainMyself:
    _order = ["fleet", "azure", "chimera", "chimerwtf"]

    def explain_yourself(self, detail_level="basic"):
        return {
            "concept": "So, uh... Hi? IDK what to say, I'm not a peoples person :/.",
            "what": "Ahem, Hi there, my name is SmhwdiBZdmpvaCBrbCBWc3BjbHB5aA==, But you can call me Dexmachina! I am the main dev of Ch-aOS, and I... I think this is a dev log? I guess I should REALLY explain myself huh? lmao... ALSO RUN EVERYTHING IN THIS NAMESPACE WITH -d advanced FOR MORE DETAILED ANSWERS.",
            "why": "Cuz 1 it's funny, 2 I want to have a better way to show y'all the Ch-aOtic chopping board for Ch-aOS (ight, imma stop with the puns), and 3 cuz I can (I need someplace to put my dev ramblings (GOT IT?)).",
            "how": "Uh... I type stuff? Like, I'm kind of typing a dict with the keys 'concept', 'what', 'why' and 'how' rn. I dunno what else to say here lol.",
            "technical": "If you REALLY want to get technical, this is just a class with a method that returns a dict with some strings in it. Nothing fancy, just some good ol' Python.",
            "equivalent": "# aint no one got it like I do babyyy",
            "learn_more": [
                "Uhhh... I'll put a lot of things inside this namespace, just run chaos explain yourself.list"
            ],
        }

    def explain_listt(self, detail_level="basic"):
        return {
            "concept": "You've mistyped it, WHAT A CONCEPT HUH?",
        }

    def explain_fleet(self, detail_level="basic"):
        return {
            "concept": "Fleet Management with Ch-aOS",
            "whay": "Ok, NOW I do need to explain myself a bit more. So, basically, I want to be able to manage a fleet of machines with Ch-aOS. Like, not just one machine, but like... a whole bunch of them. You know, like a fleet of ships, but instead of ships, it's computers. Get it? Huh? Huh?",
            "why": "Cuz it's cool, and easy (It IS NOT.), and fr, who in their right mind would want to install this binary inside of a TON of machines, CLONE the repo for Ch-obolos and secrets, set everything up and ONLY THEN run chaos apply? NOBODY. That's who. (run this with -d advanced, please)",
            "how": "So, the idea is simple (for you): declare smth akin to the example I'll put below inside of your chobolo, and then run chaos apply tags --fleet -c chobolo.yml, for me is more like 'set a fallback of @local if not fleet is defined + no --fleet passed', 'if there is a fleet, read it, parse it, and for each host inside of it, run pyinfra remotely with the right parameters'.",
            "examples": [
                {
                    "yaml": """# Example fleet declaration inside of a chobolo.yaml
fleet:
    parallelism: 5 # this is the max number, sadge
    # Oh, also, this ^ falls back to 0 if not defined
    hosts:
        - host1:
            ssh_user: root
            ssh_port: 22
            ssh_key: /path/to/key
        - host2:
            ssh_user: admin
            ssh_port: 2222
            ssh_key: /path/to/another/key
        # and so on and so forth...
                """
                }
            ],
            "equivalent": "# Like I said before, AINT NO ONE GOT IT LIKE I DO BABYYY",
        }

    def explain_azure(self, detail_level="basic"):
        return {
            "concept": "Azure Integration with Ch-aOS",
            "what": "So, yk how sops can use azure key vault as a secrets backend? Well, I wanna do the same for Ch-aOS. Like, you could have your secrets stored in Azure Key Vault, and then when you run chaos secrets rotate-add az azure_key (idk, im not an azure expert), it would configure sops to use it.",
            "why": "Cuz some people use Azure, and I wanna make sure Ch-aOS works well for them too. Plus, it's always good to have more options for secrets management.",
            "how": "Basically, I'd need to implement support for Azure Key Vault in the secrets management part of Ch-aOS. This could involve using the Azure SDK to authenticate and access the key vault, and then integrating that with sops, but hey if they got a CLI, I can make a better integration hehe (PLEASE don't look too closely at the integration with bw bws and op, they're great, but you might get a heat stroke because of how FIRE they are).",
        }

    def explain_chimera(self, detail_level="basic"):
        return {
            "concept": "Ch-imera: The chobolo to nix compiler",
            "what": "IKR, 'WHAAAT?', right? So, Ch-imera is this idea I have to create a tool that can take a chobolo (the YAML files used by Ch-aOS) and convert them into Nix expressions. This would allow users to leverage the power of Nix's declarative package management while still using the familiar chobolo format.",
            "why": "Cuz Nix is awesome, and I wanna make it easier for people to use Nix in general, not just with Ch-aOS. Plus, it would open up a whole new world of possibilities for managing system configurations in a reproducible way.",
            "how": "The idea is simple in paper (like all dev ideas): step 1 get a new CLI entrypoint called chimera, step 2 get all of Ch-aOS's plugins' chobolos keys to have a nix equivalent (not that hard if you think declaratively tbh), step 3 each plugin would implement its own chobolo to nix compilation (COOL AF RIGHT?), step 4 combine all of them into a single Nix expression that represents the entire system configuration as defined by the chobolo. Easy peasy (No it isnt).",
            "equivalent": "# YALL KNOW THE DRILL BY NOW AINT NO ONE GOT IT LIKE I DO BABYYY",
        }

    def explain_chimerwtf(self, detail_level="basic"):
        return {
            "concept": "I KNOW, WEIRD AND HARD, LET ME EXPLAIN",
            "what": "Now, i KNOW what you're thinking, 'Dex, how in the nine hells of Dante do you plan to do mini-compilers for each plugin? That sounds wayyy too complex for a fith semester student!' Well, first of all, SIXTH semester, tyvm, and second of all, hear me out. I have a cool ass professor by my side (confirmed btw), he teaches about COMPILERS, and has migrated from ARCH to NIXOS (yk what's the first core i've done? THAT'S RIGHT, ARCH), plus I'll use this for my undergrads, so I DO have a drive for it",
            "why": "Uhhh... Cause more people should use NixOS, since its very kool :3",
            "how": "I already explained how in 'yourself.chimera', go read the docs damn /rolls eyes",
        }
