"""A lightweight, decoupled wrapper for dynamic class assignment."""
import functools
from types import FunctionType


"""These are tied to the operation of this module (along with __class__) - try not to step on them!"""
_ACTIVE_CLASS = "_active_class"
_PROTECTED_SELF = "_protected_self"
_SHOULD_DECORATE_FLAG = "_protect_self_reference"
QUEEN = "queen"
DRONE = "drone"


"""These are just default settings for the wrapper. It might help to read these, but you're fine without them."""
DEFAULT_NO_DECORATES_ON_ANY_IN_INHERITANCE_TREE = {  # These attrs are never wrapped to inject self.queen for self.
    "__new__", "__init__", "__del__", "__dict__",  # However, if called on "self" instead of "self.drone",
    "__getattr__", "__delattr__", "__getattribute__", "__setattr__",  # and the queen is designed not to forward it
    QUEEN, DRONE,  # then the queen's method will be called and self will be queen regardless of self.queen injection.
    "__eq__", "__hash__", "__ne__",  # (see MAGIC_NO_REDIRECT_METHODS for methods which queen will not forward)
    "__str__", "__repr__", "__format__",
    "__set__", "__delete__", "__get__",
    "__prepare__", "__init_subclass__",
    "__traceback__", "__wrapped__ ",
    "__qualname__", "__self__",
    "__defaults__", "__kwdefaults__",
    "__globals__", "__closure__",
    "__subclasshook__",
}
DEFAULT_FORCED_DECORATES_ON_DECORATED_CLASS_ONLY = {  # These methods are always affected in an @assimilated class.
     "__new__", "__init__", "__setattr__"  # new and init and both called as controlled by queen,
}  # and setattr will always check if attr should be wrapped. However, you can still access them through self.drone.


"""If you plan on using magic methods, this section of constants is for you!"""
REDIRECT_METHODS = {  # These all auto-redirect if bound to an instance which implements them.
    "__isabstractmethod__",
    "__objclass__", "__set_name__",
    "__mro_entries__", "__classcell__", "__class_getitem__",
    "__func__", "__annotations__",
    "__file__", "__module__",
    "__copy__", "__deepcopy__",
    "__set__", "__delete__", "__get__",
    "__delitem__", "__setitem__", "__missing__", "__getitem__",
    "__contains__", "__reversed__", "__iter__",
    "__anext__", "__next__", "__aiter__",
    "__length_hint__", "__len__",
    "__getinitargs__", "__getnewargs__", "__getstate__", "__setstate__", "__reduce__", "__reduce_ex__",
    "__enter__", "__exit__", "__aenter__", "__aexit__",
    "__call__", "__await__",
    "__float__", "__int__", "__index__",
    "__complex__", "__invert__",
    "__ceil__", "__floor__", "__trunc__", "__round__",
    "__abs__", "__pos__", "__neg__",
    "__lt__", "__le__", "__gt__", "__ge__",
}
REDIRECT_I_R_ABLE_METHODS = {  # These all auto-redirect if bound to an instance which implements them, along with
    "__add__", "__sub__",  # their in-place- and right- versions. (For example: (__add__, __iadd__, __radd__))
    "__mul__", "__matmul__",
    "__truediv__", "__floordiv__",
    "__mod__", "__divmod__",
    "__pow__",
    "__lshift__", "__rshift__",
    "__and__", "__xor__"
}
MAGIC_CONTROLLED_REDIRECT_METHODS = {  # These end up redirecting either through wrapper implementation or __class__.
    "__class__", "__dict__", "__doc__",
    "__repr__", "__str__", "__format__"
    "__bool__", "__sizeof__",  # bool evaluates to False for unbound BorgPods instances, redirects otherwise.
    "__name__", "__dir__",
    "__mro__", "__bases__",
    "__instancecheck__", "__subclasscheck__",
}
MAGIC_NO_REDIRECT_METHODS = {  # These do not redirect either because they cannot for consistency / "should not".
    "__prepare__", "__init_subclass__",  # I believe these will be handled by __class__ - untested.
    "__traceback__", "__wrapped__ ",
    "__qualname__", "__self__",
    "__defaults__", "__kwdefaults__",  # I don't have a great reason for not forwarding these attrs other than utility.
    "__globals__", "__closure__",
    "__code__", "__del__", "__slots__",  # Will not support __slots__ as is.
    "__eq__", "__ne__", "__hash__",  # Hash consistency with equality requirement, and binding != for no surprises.
    "__subclasshook__", "__getattribute__",
    "__setattr__", "__delattr__", "__getattr__"
    "__weakref__", "__init__", "__new__",  # Init and new are still called in any wrapped class,
}  # you just can't access either post-init from self.__init__() as expected.
# deprecated: __unicode__ __nonzero__  __div__  __coerce__ __cmp__
# (TODO Customize?): "__copy__", "__deepcopy__",
# (TODO Customize?): "__getinitargs__", "__getnewargs__", "__getstate__", "__setstate__", "__reduce__", "__reduce_ex__"


def resist(this_function):  # Note: This is the first of 3 module attributes you should know about!
    """
    Use this @wrapper to prevent a self.queen reference being passed as self in this_function for any @assimilate class.

    :Parameters:
        :param Function this_function: A method which utilizes an object instance as the first implicit pos argument.
    :rtype: Function
    :return Function this_function: The same method, but with a flag attribute to prevent self.queen injection wrapper.
    """
    this_function._protect_self_reference = False
    return this_function


def _should_protect_self_access(attr, value):
    """
    Determines if value method tied to class/instance attribute should be wrapped to protect access to self by
        substituting self.queen. True if:
            attr is not hardcoded to be ignored, and
            value is an instance of FunctionType (as are methods utilizing self), and
            value has not been flagged with _SHOULD_DECORATE_FLAG ("_protect_self_reference") as False.

    :Parameters:
        :param str attr: The attribute key to be associated with value in the relevant Class.
        :param value: Value attr is being set to. Modified if value's key, type, and attributes meet requirements
            listed at top of docstring.
    :rtype: bool
    :return: True if value and attr key meet requirements at top of docstring, else False.
    """
    return (
        attr not in DEFAULT_NO_DECORATES_ON_ANY_IN_INHERITANCE_TREE and isinstance(value, FunctionType)
        and getattr(value, _SHOULD_DECORATE_FLAG, True)
    )


def _safe_self_access_decorator(wrapped_method):
    """
    Replaces method "self" arguments with "self.queen" implicitly due to the overwhelmingly more common use intentions.

    :param Function wrapped_method: The method which utilizes self to be modified.
    :rtype: Function
    :return: The wrapped method.
    """
    @functools.wraps(wrapped_method)
    def method_wrapper(self, *args, **kwargs):
        if hasattr(self, QUEEN):
            return wrapped_method(self.queen, *args, **kwargs)
        return wrapped_method(self, *args, **kwargs)
    return method_wrapper


def _modify_methods_for_self_reference(this_class):
    """
    Modifies relevant methods in this_class to protect references to self per method if _should_protect_self_access
        returns True when passed *(attribute_key, method_value).

    :param Class this_class: @assimilate decorated class or parent class with methods to be protected if self.queen
        exists in the instance.
    :rtype: None
    :return: None
    """
    for c_attribute, c_method in this_class.__dict__.copy().items():
        if _should_protect_self_access(c_attribute, c_method):
            setattr(this_class, c_attribute, _safe_self_access_decorator(c_method))
            c_method._protect_self_reference = False


def _borg_pod_set_with_safe_self_access(wrapped_method):
    """
    Wrapper for __setattr__ methods in @assimilate decorated classes to apply self.queen injection wrapper on any
        relevant instance methods set during runtime.

    :param Function wrapped_method: A @assimilate decorated class's __setattr__ method.
    :rtype: Function
    :return: The decorated __setattr__ method.
    """
    @functools.wraps(wrapped_method)
    def setter_wrapper(self, attribute, value):
        if _should_protect_self_access(attribute, value):
            value = _safe_self_access_decorator(value)
        wrapped_method(self, attribute, value)
    return setter_wrapper


def assimilate(_wrapped_class=None, *, default_class=None):  # Note: This is the main module attribute you should know!
    """
    Wraps a class such that its instances can be converted to another @assimilate'd class while preserving its
        attributes and ID, and performing that conversion across all references to that instance. Unlike the singleton
        pattern, there can be multiple unique IDs per any @assimilate class. Unlike the borg idiom, those sharing a set
        of attributes also share an ID. This gives objects a dynamic (over time, but not over shared states) class
        decoupled from each potential class's implementation.


    :Parameters:
        :param Class _wrapped_class: The class with instances to be incorporated into individual borg pods.
        :param Class default_class: The class of the proxy object to be searched for if _base_class is not provide at
            init (instance class conversion) time, as well as the class of the proxy object to be created if no
            instance is found.
    :rtype: Class
    :return: wrapped_class with the proper state-setting and self-reference-preserving wrappers around instance methods.


    :What:
        A new design pattern / idiom / anti-pattern / affront to the light of Heaven, depending on your view, wrapped up
            in an easy to deploy decorator! It's a:
                Borg (shared state, unique instances)
                Singleton (shared state, shared ID / memory location)
                Bridge (object interacted with does not contain the implementation logic)
        It's also:
            not a Borg (ID/memory location is consistent between shared states) and
            not a Singleton (can create multiple instances) and
            not a Bridge. (object's implementation and abstraction are bound, and at the same time completely free to
                change due to borg-like state-sharing and the strengths of __new__ for controlling return and init())

        :What^2:
            You might ask, isn't this a State? A strategy? Take a look at the implementation. In terms of developer
                strain, working with a state machine is... not ideal. It's a hassle to implement, and in most cases it's
                preferable to treat everything as if it were the same object and not need to worry about what is being
                accessed from where. Why can't I put a decorator above the class and be done with it? Why can't I change
                a class on the fly? Now you can. The Borg Singleton State Facade. THE BORG POD.


    :How to Use:
        Take a class you wish to use in a borg pod, and put @assimilate above the class definition - that's the gist. If
            you want to create a new borg pod (a new shared state and shared ID set) you may just call:
                YourAssimilatedClass(); when you wish to convert an instance of another borg pod class to that class:
                YourAssimilatedClass(other_assimilated_instance); you may optionally use:
                YourAssimilatedClass(some, args, queen=other_assimilated_instance, key=word, arguments=here); or:
                YourAssimilatedClass(some, args, other_assimilated_instance, other, args, kw=args); as,
            if queen is not provided, the wrapper will pick out and remove the first _base_class instance (if
            _base_class provided as kwarg) or default_class (if not provided) instance from args. You may also just
            call YourAssimilatedClass(), and it will instance a new base_class() and use it as the new borg pod. The
            borg pod instance, not the YourAssimilatedClass() instance, is returned from __new__() after __init__() is
            called to maintain reference consistency.

        You need not modify your __init__() arguments for the wrapper, as the queen will be removed if provided, the
            first instance of class _base_class if not (if provided as kwarg; wrapper's default_class if not), or it
            will silently create a new _base_class (or default_class) if neither a queen was explicitly provided nor was
            a queen instance found. Nothing associated with the wrapper will get through to your init, and nothing
            about the instance will be changed* by the wrapper once it reaches one of your __init__ calls.

                *__setattr__() will modify self-methods set in a class / instance to inject self.queen if the new
                    self-method is not pre-wrapped with @resist.


    :Best Practices:
        1. Any of the attributes set by this wrapper (self.queen, self.drone, _protected_self, _active_class, __doc__,
            __class__ property, and _protect_self_reference [the last is on methods]) should not be changed except
            through the interface (@assimilate, @resist) offered by this module - and any method or class should only be
            explicitly decorated a single time. (You may subclass and decorate from both unwrapped and wrapped classes -
            just don't put @assimilate\n@assimilate\nclass YourClass() and be surprised when you have a bad time.)

        2. Because of how the self.queen injection works, the best course of action is letting the interpreter fill in
            super() arguments as in super().parent_method() instead of explicitly calling
            super(self.__class__, self).parent_method(). This will automatically select the parent class method based on
            the owning class of the method being called from rather than the class of self.

        3. Definitely needs new-style classes, almost certainly needs Python >= 3, needs testing for <3.6.


    :How it Works:
        The 'borg pod' is a bridge or state-machine-like object, which stores a protected reference to both itself and
            the current acting class instance. It too shares an internal state with the @assimilate'd instance, and will
            search that instance for methods not found in its class. You may subclass or change the proxy class, and set
            per-wrapper the default proxy class to use if no class is provided at __new__ time by setting the optional
            default_class decorator argument.

        For consistency, all references to self passed into a method are converted to the proxy's self. This allows for
            chaining calls and setting references in other objects without the overhead of explicitly calling
            self.queen, as the object should always be accessed through self.queen to behave as expected. You may use
            the @resist wrapper on any method to prevent this from implicitly happening. self.drone will explicitly
            access the current de facto class, and self.queen will access the proxy object. As the need for an implicit
            conversion mechanism implies, it is suggested that self references be converted to self.queen unless there
            is a significant reason to do so. Although the object will still have a self.queen reference to recover its
            'borg pod' object ID, this could be a frustrating source of identity bugs!

        @assimilate decorated classes are subclass, __magic__ and inspection-friendly. The "queen" class instance will
            adopt the __class__*,  __doc__, __dir__, methods, and even magic methods** of the drone class instance.

                *if inspected - they don't really set their __class__! I'm actually not sure if it is even accessible
                    through normal methods [as in overwriting inherited __slots__ names] - but super(), etc still work.

                **if not found in MAGIC_NO_REDIRECT_METHODS at the top of the module. Most notable among them are
                    __eq__() and __hash__(). For reasoning behind these choices, please read the Python 3 documentation
                    (https://docs.python.org/3/reference/datamodel.html) on customizing __hash__ and __eq__ - keeping
                    in the mind the context of maintaining a consistent identity - for why.

    :Reasoning for the Madness:
        I had an image full of objects of ambiguous and potentially changing classes depending on the state, values,
            and classes of other objects. While the options of {computing the context per object until their states
            settled, holding off on initiating what would be an @assimilate'd class instance until the object's class
            was no longer ambiguous, depth-first classifying per object the correct static class in __new__, or
            creating some sort of stateful monstrous mega-class-conglomerate} were all available, it was useful to be
            able to treat an object under the assumption that it was a certain class to bootstrap the context
            process and not need to worry about where I was accessing what attributes. It's the same object, why can't I
            use self? There is a clear need for the ability to change the effective class and methods of an object
            without going through the trouble of fixing all pointers to the new Class instance and without needing to
            explicitly transfer states and couple the potential classes. The solution? The Borg Pod.

    :Credits:
        borg_pod module by Andrew M. Hogan. (borg_pod Copyright 2018 Hogan Consulting Group)
    """
    if default_class is None:
        default_class = BorgPod

    def borg_pod_decorator(wrapped_class):
        """Modify methods and attributes of wrapped_class to support the borg pod interface."""
        def _setup_pod_in_new(wrapped_new):
            """Modifies the __new__ method to return an instance of the borg pod object rather than wrapped_class."""
            @functools.wraps(wrapped_new)
            def new_wrapper(cls, *args, queen=None, _base_class=None, **kwargs):
                if _should_be_self_class_unless_called_from_child_class != cls:
                    # This was called from a subclass; better just return the new object without anything crazy.
                    return wrapped_new(cls)
                # Is this the False queen?
                if queen is None:
                    # Just be glad this isn't a spit() function.
                    if _base_class is None:
                        _base_class = default_class
                    for ids, arg in enumerate(args):
                        if isinstance(arg, _base_class):
                            # We have found the queen which evaluates to True. Remove from args so __init__ is okay.
                            queen = arg
                            args = args[:ids] + args[ids + 1:]
                            break
                    else:
                        # ...Then we shall forge our own queen.
                        queen = _base_class({})
                new_object = wrapped_new(cls)
                new_object.__init__(*args, queen=queen, **kwargs)
                return queen
            return new_wrapper

        def _assimilate_in_init(wrapped_init):
            """Modifies the __init__ method to ensure that the instance dict is converted if not called by subclass."""
            @functools.wraps(wrapped_init)
            def init_wrapper(self, *args, queen=None, **kwargs):
                if queen is None:
                    # Prevents recursive loop in wrapped Parent classes.
                    return wrapped_init(self, *args, **kwargs)
                queen.__doc__ = self.__doc__
                self.__dict__ = queen.__dict__
                self._active_class = self
                self.queen = self._protected_self.queen
                self.drone = self._protected_self.drone
                return wrapped_init(self, *args, **kwargs)
            return init_wrapper

        # These ancestor lists will always be the ones available when the class method is called - pretty handy!
        _all_ancestors = wrapped_class.mro()
        _should_be_self_class_unless_called_from_child_class, ancestors = _all_ancestors[0], _all_ancestors[1:]

        # Instance method self-reference protector
        _modify_methods_for_self_reference(wrapped_class)

        # Some special magic methods that make everything sweeter with a little forced decoration.
        setattr(wrapped_class, '__new__', _setup_pod_in_new(wrapped_class.__new__))
        setattr(wrapped_class, '__init__', _assimilate_in_init(wrapped_class.__init__))
        # setattr(wrapped_class, '__hash__', lambda x: hash(x.queen))
        # setattr(wrapped_class, '__eq__', lambda x, y: x.queen is y.queen if hasattr(y, QUEEN) else False)
        setattr(wrapped_class, '__setattr__', _borg_pod_set_with_safe_self_access(wrapped_class.__setattr__))
        for this_method in DEFAULT_FORCED_DECORATES_ON_DECORATED_CLASS_ONLY:
            getattr(wrapped_class, this_method)._protect_self_reference = False

        for ancestor in ancestors:
            if ancestor is not object:  # TODO: Check against all builtin types? (~Submit a pull request~)
                _modify_methods_for_self_reference(ancestor)

        return wrapped_class

    if _wrapped_class is None:
        # An optional keyword argument was provided!
        return borg_pod_decorator
    return borg_pod_decorator(_wrapped_class)


def _set_magic_methods(wrapped_class, names):
    """Betcha can't have just one!"""
    for name in names:
        _set_magic_method(wrapped_class, name)


def _set_magic_method(wrapped_class, name):
    """Aw..."""
    setattr(wrapped_class, name, _magic_dictate(lambda self: self._active_class, name))


def _magic_dictate(wrapped_method, name):
    """It's Wing-gar-dium Levi-o-sa, make the 'gar' nice and long."""
    @functools.wraps(wrapped_method)
    def magic_wrapper(self, *args, **kwargs):
        try:
            return getattr(wrapped_method(self), name)(*args, **kwargs)
        except RecursionError:
            _unbound_access_error(self, name)
    return magic_wrapper


def _unbound_access_error(this_instance, this_method_name):
    """Where my assimilates at?"""
    raise AttributeError(
        "Instances of Class {} cannot call method {} without being bound to another object with that method.".format(
            this_instance.__class__, this_method_name
        )
    )


def _redirect_magic_methods(wrapped_class):
    """You really expected a newly-created, implementation-detail, private wrapper to have documentation?"""
    for name in REDIRECT_I_R_ABLE_METHODS:
        r_name = "__r" + name[2:]
        i_name = "__i" + name[2:]
        _set_magic_methods(wrapped_class, (name, r_name, i_name))
    for name in REDIRECT_METHODS:
        _set_magic_method(wrapped_class, name)
    return wrapped_class


@_redirect_magic_methods
class BorgPod(object):  # Note: This is the last module attribute you should know! It's all test material from here.
    """
    This is a hidden access point to instances of classes bound by @assimilate. It is a state machine, facade, proxy,
        bridge, and none of the above at the same time! Unless a method is decorated with @resist, all implicitly
        passed references of self are converted to an instance of this class (or the provided _base_class or
        default_class). It will still access your instances methods and attributes! It's just a way of simplifying
        development overhead for implementing design patterns like strategy which should frankly be built into the
        language. The entire group of objects in a state machine system refer to the same thing. Why do I have to change
        the way I access attributes? Why do I even have to set up that division in the first place?
    """
    # _base_borgs = set()  # If you were to instance BorgPods off of existing objects, I'd use a hash lookup in __new__.

    def __init__(self, _shared_state=None):
        self.__dict__ = _shared_state if _shared_state is not None else {}
        self._active_class = self
        self._protected_self = self
        super().__init__()

    @property
    def queen(self):
        """The queen is like a decoupled proxy object for accessing attributes and methods of the borg pod."""
        return self._protected_self

    @property
    def drone(self):
        """The drone controls both the attributes and methods of the borg pod during its lifetime as _active_class."""
        return self._active_class

    @property
    def __class__(self):
        """This isn't where the magic happens, but it does make things much more inspection-friendly."""
        if self._active_class is not self._protected_self:
            return self._active_class.__class__
        return BorgPod

    def __bool__(self):
        """Returns False if not bound to an object."""
        if self._active_class is not self._protected_self:
            return bool(self._active_class)
        return False

    def __getattr__(self, name):
        """__getattr__ is called if 'name' was not found in this class. Magic methods use another route due to magic."""
        try:
            return getattr(self._active_class, name)
        except RecursionError:
            _unbound_access_error(self, name)

    def __hash__(self):
        """Identical borg pod objects are always sent to the same location in a hash table."""
        return hash((BorgPod.__name__, id(self)))

    def __eq__(self, other):
        """Identical borg pod objects always evaluate as the same object."""
        return hash(self) == hash(other)

    def __str__(self):
        """Calls drone's __str__ or defaults small description with class and ID."""
        if self._protected_self is not self._active_class:
            return self._active_class.__str__()
        return "<Unbound {} object #{}>".format(self._protected_self.__class__.__name__, id(self._protected_self))

    def __repr__(self):
        """Calls drone's __repr__ or defaults str."""
        if self._protected_self is not self._active_class:
            return self._active_class.__repr__()
        return self.__str__()

    def __format__(self, format_spec):
        """Calls drone's __format__ or defaults super()."""
        if self._protected_self is not self._active_class:
            return self._active_class.__format__(format_spec)
        return super().__format__(format_spec)

    def __sizeof__(self):
        """Calls drone's __sizeof__ or defaults super()."""
        if self._active_class is not self._protected_self:
            return self._active_class.__sizeof__()
        return super().__sizeof__()


class _PerfectGreekInfluencedChalkDrawingOfFace(object):  # Abandon all hope of helpful docs/names, ye' who enter here.
    """The first step towards drawing any circle."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shape_type = "pre-circle"

    def self_method(self):
        return self


@assimilate(default_class=BorgPod)
class _Circle(_PerfectGreekInfluencedChalkDrawingOfFace):
    """
    The Borg Pod does not care about unique inheritance. Your biological distinctiveness has been added to the
        collective.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shape_type = "circle"

    @staticmethod
    def info():
        print("I AM CIRCLE.")

    # def self_method(self):  # Oh no! But inheritance still works.
    #     return self

    def __str__(self):
        if hasattr(self, DRONE):
            return "<{} object #{} bound to same address as Queen id #{}>".format(
                self.drone.__class__.__name__, id(self.drone), id(self.queen)
            )
        return "<Unassimilated {} object #{}>".format(self.__class__.__name__, id(self))

    __repr__ = __str__


@assimilate
class _Ellipse(_Circle):
    """
    The Borg Pod does not care about unique inheritance. Your biological distinctiveness has been added to the
        collective.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shape_type = "ellipse"


@assimilate
class _AlphaNumeric(object):
    """
    The Borg Pod does not care about unique signatures. Your technological distinctiveness has been added to the
        collective.
    """
    def __init__(self):
        self.shape_type = "character"

    @staticmethod
    def info():
        print("I AM CHARACTER.")

    def self_method(self):
        self.info()
        return self

    def __add__(self, other):
        print("IN _ALPHANUMERIC __add__(): {} + {}".format(self, other))
        return 1

    def __str__(self):
        if hasattr(self, DRONE):
            return "<{} object #{} bound to same address as Queen id #{}>".format(
                self.drone.__class__.__name__, id(self.drone), id(self.queen)
            )
        return "<Unassimilated {} object #{}>".format(self.__class__.__name__, id(self))

    __repr__ = __str__


@assimilate
class _Punctuation(object):
    """The Borg Pod does care about resistance due to the current political climate, but stresses its futility."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shape_type = "punctuation"

    @staticmethod
    def info():
        print("I AM PUNCTUATION.")

    @resist
    def self_method(self):
        return self

    def __str__(self):
        if hasattr(self, DRONE):
            return "<{} object #{} bound to same address as Queen id #{}>".format(
                self.drone.__class__.__name__, id(self.drone), id(self.queen)
            )
        return "<Unassimilated {} object #{}>".format(self.__class__.__name__, id(self))

    __repr__ = __str__


def _compare_seq(sequence, sequence_2=None):
    """
    Print whether items in the iterable are/are not the same as the next element in the same list,
        or the matching-index elements in sequence_2 (if not None).
    """
    if sequence_2 is None:
        for ob_a, ob_b in zip(sequence, sequence[1::] + [sequence[0]]):
            print("{}: {} is {}".format(ob_a is ob_b, ob_a, ob_b))
    else:
        for ob_a, ob_b in zip(sequence, sequence_2):
            print("{}: {} is {}".format(ob_a is ob_b, ob_a, ob_b))


def _assert_seq(sequence, sequence_2=None, *, assert_val=True):
    """
    Assert that items in the iterable are/are not the same as the next element in the same list,
        or the matching-index element in sequence_2 (if not None).
    """
    if sequence_2 is None:
        for ob_a, ob_b in zip(sequence, sequence[1::] + [sequence[0]]):
            assert (ob_a is ob_b) == assert_val, "Assertion that {} is {} did not match provided value of {}.".format(
                ob_a, ob_b, assert_val
            )
    else:
        for ob_a, ob_b in zip(sequence, sequence_2):
            assert (ob_a is ob_b) == assert_val, "Assertion that {} is {} did not match provided value of {}.".format(
                ob_a, ob_b, assert_val
            )


def _convert_seq(sequence, new_class):
    """Convert the iterable to a new class!"""
    return [new_class(obj) for obj in sequence]


def _identity_crisis_test(num_objects):
    """Test creation, identity, and inheritance control flows."""
    test_objects_original = [BorgPod() for _ in range(num_objects)]
    print("\n____\nBEGIN @ASSIMILATE IDENTITY TESTS\n")
    print("Are they unique objects?")
    _assert_seq(test_objects_original, assert_val=False)

    print("\nConvert To Circles->")
    test_objects_circle = _convert_seq(test_objects_original, _Circle)
    print("Are they unique objects?")
    _assert_seq(test_objects_circle, assert_val=False)
    print("Is equal to original list?")
    _assert_seq(test_objects_circle, test_objects_original)
    print("what if we return self?")
    self_list_ambiguous = [obj.self_method() for obj in test_objects_circle]
    print("Are they equal to the old version?")
    _assert_seq(self_list_ambiguous, test_objects_circle)
    print("Can we still use instances of an undecorated parent class if a subclass is decorated with @assimilate?")
    test_objects_undecorated_parent_class = [_PerfectGreekInfluencedChalkDrawingOfFace() for _ in range(num_objects)]
    self_list_face = [obj.self_method() for obj in test_objects_undecorated_parent_class]
    for face_return, original_face in zip(self_list_face, test_objects_undecorated_parent_class):
        assert not isinstance(face_return, BorgPod)
        assert isinstance(face_return, _PerfectGreekInfluencedChalkDrawingOfFace)
        assert not isinstance(original_face, BorgPod)
        assert isinstance(original_face, _PerfectGreekInfluencedChalkDrawingOfFace)
        assert face_return is original_face
    print("What if we use a child class decorated with @assimilate when a parent class is also decorated?")
    test_objects_decorated_subclass = [_Ellipse() for _ in range(num_objects)]
    print("Is the self-return converted properly?")
    self_list_sub = [obj.self_method() for obj in test_objects_decorated_subclass]
    _assert_seq(self_list_sub, test_objects_decorated_subclass)
    print("Can the sub-class still be converted?")
    print("\nConvert To Characters->")
    test_objects_subclass_converted = _convert_seq(test_objects_decorated_subclass, _AlphaNumeric)
    _assert_seq(test_objects_subclass_converted, test_objects_decorated_subclass)
    print("Nice! Let's test some more attributes on the original circle objects.")
    return test_objects_original, test_objects_circle


def _magic_test(test_objects_circle, test_objects_original):
    """Test magic method binding, class, and inspection attributes."""
    print("\n____\nBEGIN MAGIC TESTS")
    print("First we'll convert to a class with magic methods, and assert a couple common sense identity attrs again.")
    print("\nConvert To Characters->")
    test_objects_characters = _convert_seq(test_objects_circle, _AlphaNumeric)
    print("Are they still unique objects with their previous IDs?")
    _assert_seq(test_objects_characters, assert_val=False)
    _assert_seq(test_objects_characters, test_objects_circle)
    _assert_seq(test_objects_characters, test_objects_original)

    print("Does using magic methods implemented in an @assimilated class still work? Let's try an object + 1.")
    _ = test_objects_characters[0] + 1
    print("Nice! What happens if we call a magic method on an unbound Borg Pod?")
    test_object = BorgPod()
    try:
        test_object *= 1
    except AttributeError as e:
        print("That was close! Here is our error: {}".format(e))
    else:
        raise AssertionError("The imul method should have error'd while unbound. Fortunately, I have a spare!")
    print("Does the unbound instance preserve its docstring?")
    assert test_object.__doc__ is BorgPod.__doc__
    print("Does a bound instance properly inherit the bound docstring?")
    assert test_objects_characters[0].__doc__ is _AlphaNumeric.__doc__
    assert test_object.__doc__ is not test_objects_characters[0]
    assert test_object.__doc__ is not test_objects_characters[0].__doc__
    print("Are their available dirs in line with their classes?")
    assert ([attr for attr in dir(test_objects_characters[0]) if
             attr not in {"queen", "drone", "_active_class", "_protected_self", "shape_type"}]
            == dir(_AlphaNumeric)), "Did you add more instance methods?"
    assert ([attr for attr in dir(test_object)
             if attr not in {"_active_class", "_protected_self", "shape_type"}]
            == dir(BorgPod)), "Did you add more instance methods?"
    print("And that means separately bound instance dirs are not the same nor equal, correct?")
    assert dir(test_objects_characters[0]) is not dir(test_object)
    assert dir(test_objects_characters[0]) != dir(test_object)
    print("And that means their respective bound classes evaluate as the same as the module-level class, correct?")
    assert test_objects_characters[0].__class__ is _AlphaNumeric
    assert test_object.__class__ is BorgPod

    return test_objects_characters


def _the_resistance_test(test_objects_characters):
    """Test the @resist decorator."""
    print("\n____\nBEGIN @RESIST DECORATOR TESTS")
    print("Let's try converting to a class with a @resist decorated method returning 'self'.")
    print("\nConvert To Punctuations->")
    test_objects_punctuation = _convert_seq(test_objects_characters, _Punctuation)
    print("First, let's assert a couple common sense identity attrs again.")
    print("Are they unique objects?")
    _assert_seq(test_objects_punctuation, assert_val=False)
    print("Is equal to character list?")
    _assert_seq(test_objects_punctuation, test_objects_characters)

    print("What if we return self from a method decorated with @resist?")
    self_list_unprotected = [obj.self_method() for obj in test_objects_punctuation]
    print("(A method decorated with @resist will not convert 'self' to the queen reference. [not suggested])")
    print("Are they unique objects?")
    _assert_seq(self_list_unprotected, assert_val=False)
    print("Do they no longer evaluate as the same object from the previous punctuation list?")
    _assert_seq(self_list_unprotected, test_objects_punctuation, assert_val=False)
    print("What if we retrieve the drones from the previous characters list?")
    drone_list_characters = [obj.drone for obj in test_objects_characters]
    print("Does it evaluate as the same to the @resist self list?")
    _assert_seq(drone_list_characters, self_list_unprotected)
    print("What if we retrieve the queen from the @resist self list?")
    self_list_restored = [obj.queen for obj in self_list_unprotected]
    print("Does it evaluate as the same to the original characters list?")
    _assert_seq(self_list_restored, test_objects_characters)


def main(num_objects=6):
    """
    Run some assertion tests and prints to demonstrate that you too can have easy, dynamic classes in existing
        infrastructure!

    :Parameters:
        :param int num_objects: The length of the list of test objects to be created.
    :rtype: None
    :return: None
    """
    print("\n____\nBEGIN TESTS\nLet's run some assertion tests and print some examples.")
    _the_resistance_test(_magic_test(*_identity_crisis_test(num_objects)))
    print("\nTests Complete\n____")


if __name__ == "__main__":
    main()
