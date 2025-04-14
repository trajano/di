"""What if I allowed containers to contain other containers?
That would simulate scopes I guess.


But how would that work especially with scoped stuff

so theoretically you can say something that would say the call groups

@application_scope
@session_scope
@call_scope

default can contain two scopes but we can do others

something along the lines of

container.resolve_with_scope("call_scope")
which will then resolve all definitions at that scope level and above.

async with config.context() as container:
  blah.
"""

from .resolver import resolve_scope

__all__ = ["resolve_scope"]
