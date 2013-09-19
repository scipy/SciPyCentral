"""
Scale for thumbs objects. The magnitude of up-vote or down-vote
is set here. Any changes in these settings also require following settings

1. Manual changes of `reputation` fields in `Revision` objects in database
2. Scale settings in `static/thumbs/thumb-actions.js`

For instance, the following code has to be run for [1]

```
from scipy_central.submission.models import Revision
for aObj in Revision.objects.all():
    aObj.reputation = aObj.set_reputation()
```

"""
REVISION_VOTE = {
    # reputation scale for revision object
    'thumb': {
        'up': 1,
        'down': 1
    },
}
