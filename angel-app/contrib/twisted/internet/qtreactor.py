try:
    # 'import qtreactor' would have imported this file instead of the
    # top-level qtreactor. __import__ does the right thing
    # (kids, don't repeat this at home)
    install = __import__('qtreactor').install
except ImportError:
    from twisted.plugins.qtreactor_stub import errorMessage
    raise ImportError(errorMessage)
else:
    import warnings
    warnings.warn("Please use qtreactor instead of twisted.internet.qtreactor",
                  category=DeprecationWarning)

__all__ = ['install']
