
def testGlobalOut():
    ''' Out is correctly mapped to the global namespace '''
    out.info("Something")
    assert 1
