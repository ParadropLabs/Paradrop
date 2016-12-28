'''
Write the CROSS-ORIGIN RESOURCE SHARING headers required
Reference: http://msoulier.wordpress.com/2010/06/05/cross-origin-requests-in-twisted/
'''


def config_cors(request):
    request.setHeader('Access-Control-Allow-Origin', '*')
    request.setHeader('Access-Control-Allow-Methods', 'GET, PUT, POST, DELETE')
    request.setHeader('Access-Control-Allow-Headers', 'Content-Type')
    request.setHeader('Access-Control-Max-Age', 2520) # 42 hours
