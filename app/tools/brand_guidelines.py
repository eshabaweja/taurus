def get_brand_guidelines(brand_id):
    if brand_id == "aniwell":
          return {
              "voice": "modern, calm, trustworthy, functional",
              "do_list": ["use 'supports'", "use 'helps'", "use 'promotes'",],
              "dont_list": ["avoid 'cure'", "avoid 'treat disease'",],
              "banned_claims": ["cure", "treat disease", "medical claims"],
              "visual_style": "clean, pet-focused, wellness aesthetic"
          }
    return {}