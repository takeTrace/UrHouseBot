class SELECTOR:
    groupTitle='.groups .result .title a'
    aLink='a::attr(href)'
    title='.td-subject a::attr(title)'
    titleLink='.td-subject a::attr(href)'
    titleTime='.td-time::attr(title)'
    usernameField='//input[@name="captcha-id"]/@value'
    userpwdField='//img[@id="captcha_image"]/@src'
# selector = dict(css=dict(
#     groupTitle='.groups .result .title a',
#     aLink='a::attr(href)',
#     title='.td-subject a::attr(title)',
#     titleLink='.td-subject a::attr(href)',
#     titleTime='.td-time::attr(title)',
#     usernameField='//input[@name="captcha-id"]/@value',
#     userpwdField='//img[@id="captcha_image"]/@src'
# ))
