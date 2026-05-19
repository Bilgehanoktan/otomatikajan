
import bcrypt

pw1 = "admin123"
pw2 = "admin1234"
h = "$2b$12$sRKqRyvDPfq2qURdhkEPlemrTzVJwRzhfOQx51BBZ51nqSH1W0jo."

print(f"admin123 matches: {bcrypt.checkpw(pw1.encode(), h.encode())}")
print(f"admin1234 matches: {bcrypt.checkpw(pw2.encode(), h.encode())}")
