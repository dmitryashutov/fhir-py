from aidbox.lib import Aidbox

ab = Aidbox(
    host='https://sansara.health-samurai.io',
    email='patient@com.com',
    password='patient')

# res = ab.resources('Entity').get('Patient')
res = ab.resources('Patient').all()

a = 0
pass