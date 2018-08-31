"""A lightweight, decoupled wrapper for dynamic class assignment."""
import functools
from types import FunctionType


_ACTIVE_CLASS = "_active_class"
_PROTECTED_SELF = "_protected_self"
_SHOULD_DECORATE_FLAG = "_protect_self_reference"
QUEEN = "queen"
DRONE = "drone"
DEFAULT_NO_DECORATES_ON_ANY_IN_INHERITANCE_TREE = {
    "__new__", "__init__", "__getattr__", "__delattr__", "__getattribute__", "__del__", QUEEN, DRONE, "__setattr__",
    "__dict__", "__str__", "__repr__", "__set__", "__eq__", "__hash__", "__init__", "__new__"
}
DEFAULT_FORCED_DECORATES_ON_DECORATED_CLASS_ONLY = {
     "__new__", "__init__", "__hash__", "__eq__", "__setattr__"
}


def resist(this_function):
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


def assimilate(_wrapped_class=None, *, default_class=None):
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
                YourAssimilatedClass()

        When you wish to convert an instance of another borg pod class to that class, use
                YourAssimilatedClass(other_assimilated_instance). You may optionally use
                YourAssimilatedClass(some, args, queen=other_assimilated_instance, key=word, arguments=here), or
                YourAssimilatedClass(some, args, other_assimilated_instance, other, args, kw=args) and
            the wrapper will pick out and remove the first _base_class instance (if _base_class provided as kwarg) or
            default_class (if not provided) instance from args. You may also just call YourAssimilatedClass(), and it
            will instance a new base_class() and use it as the new borg pod. The borg pod instance, not the
            YourAssimilatedClass() instance, is returned from __new__() after __init__() is called to maintain reference
            consistency.

    :Best Practices:
        1. Any of the attributes set by this wrapper (self.queen, self.drone, _protected_self, _active_class, and
            _protect_self_reference [the last is on methods]) should not be changed except through the interface
            (@assimilate, @resist) offered by this module.
        2. Because of how the self.queen injection works, the best course of action is letting the interpreter fill in
            super() arguments as in super().parent_method() instead of explicitly calling
            super(self.__class__, self).parent_method(). This will automatically select the parent class method based on
            the owning class of the method being called rather than the class of self, which would result in an endless
            loop of looking up the method in the proxy object, looking up the method in the proxy object's
            active class, calling that method, and then inevitably calling the super() method again to repeat the cycle.
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
        setattr(wrapped_class, '__hash__', lambda x: hash(x.queen))
        setattr(wrapped_class, '__eq__', lambda x, y: x.queen is y.queen if hasattr(y, QUEEN) else False)
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


class BorgPod(object):
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
        if _PROTECTED_SELF not in self.__dict__:
            self._protected_self = self

    @property
    def queen(self):
        """The queen is like a decoupled proxy object for accessing attributes and methods of the borg pod."""
        return self._protected_self

    @property
    def drone(self):
        """The drone controls both the attributes and methods of the borg pod during its lifetime as _active_class."""
        return self._active_class

    def __getattr__(self, name):
        """__getattr__ is called if 'name' was not found in this class."""
        if _ACTIVE_CLASS in self.__dict__:
            active_class = self.__dict__[_ACTIVE_CLASS]
            if active_class is self.__dict__[_PROTECTED_SELF]:
                raise AttributeError("Base borg-pod does not have attribute {}.".format(name))
            if hasattr(active_class, name):
                return getattr(active_class, name)
        raise AttributeError("Base borg-pod does not have attribute {}.".format(name))

    def __str__(self):
        if self._protected_self is not self._active_class:
            return self._active_class.__str__()
        return "<Unbound {} object #{}>".format(self._protected_self.__class__.__name__, id(self._protected_self))

    __repr__ = __str__

    def __hash__(self):
        """Identical borg pod objects are always sent to the same location in a hash table."""
        return hash((self.__class__.__name__, id(self)))

    def __eq__(self, other):
        """Identical borg pod objects always evaluate as the same object."""
        return hash(self) == hash(other)


class _PerfectGreekInfluencedChalkDrawingOfFace(object):
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
            return "<{} object #{} linked to {} #{}>".format(
                self.drone.__class__.__name__, id(self.drone), self.queen.__class__.__name__, id(self.queen)
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

    def this_class_has_a_unique_method_to_use_after_sorting_with_a_polymorphic_one_and_nobody_can_stop_it(self):
        print("YOU WERE SUPPOSED TO INCORPORATE THEIR DISTINCTIVENESS, NOT DESTROY IT!")
        return self.info

    def __str__(self):
        if hasattr(self, DRONE):
            return "<{} object #{} linked to {} #{}>".format(
                self.drone.__class__.__name__, id(self.drone), self.queen.__class__.__name__, id(self.queen)
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
            return "<{} object #{} linked to {} #{}>".format(
                self.drone.__class__.__name__, id(self.drone), self.queen.__class__.__name__, id(self.queen)
            )
        return "<Unassimilated {} object #{}>".format(self.__class__.__name__, id(self))

    __repr__ = __str__


def _compare_seq(sequence, sequence_2=None):
    """Print whether items in the iterable are/are not the same as the next element!"""
    if sequence_2 is None:
        for ob_a, ob_b in zip(sequence, sequence[1::] + [sequence[0]]):
            print("{}: {} is {}".format(ob_a is ob_b, ob_a, ob_b))
    else:
        for ob_a, ob_b in zip(sequence, sequence_2):
            print("{}: {} is {}".format(ob_a is ob_b, ob_a, ob_b))


def _assert_seq(sequence, sequence_2=None, *, assert_val=True):
    """Assert that items in the iterable are/are not the same as the next element!"""
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


def main(num_objects=6):
    """
    Run some assertion tests and prints to demonstrate that you too can have easy, dynamic classes in existing
        infrastructure!

    :Parameters:
        :param int num_objects: The length of the list of test objects to be created.
    :rtype: None
    :return: None
    """
    test_objects_original = [BorgPod() for _ in range(num_objects)]
    print("Let's run some assertion tests and print some examples.")
    print("Are they unique objects?")
    _assert_seq(test_objects_original, assert_val=False)

    print("\nTo Circle-")
    test_objects_circle = _convert_seq(test_objects_original, _Circle)
    print("Are they unique objects?")
    _assert_seq(test_objects_circle, assert_val=False)
    print("Is equal to old version?")
    _assert_seq(test_objects_circle, test_objects_original)
    print("what if we return self?")
    self_list_ambiguous = [obj.self_method() for obj in test_objects_circle]
    print("Are they equal to the old version?")
    _compare_seq(self_list_ambiguous, test_objects_circle)
    print("Can we still use instances of a parent class if a subclass is decorated with @assimilate?")
    test_objects_undecorated_parent_class = [_PerfectGreekInfluencedChalkDrawingOfFace() for _ in range(num_objects)]
    self_list_face = [obj.self_method() for obj in test_objects_undecorated_parent_class]
    print(self_list_face)
    print("What if we use a child class decorated with @assimilate when a parent class is also decorated?")
    test_objects_decorated_subclass = [_Ellipse() for _ in range(num_objects)]
    self_list_sub = [obj.self_method() for obj in test_objects_decorated_subclass]
    print(self_list_sub)
    print("Nice!")

    print("\nTo Characters-")
    test_objects_characters = _convert_seq(test_objects_circle, _AlphaNumeric)
    print("Are they unique objects?")
    _assert_seq(test_objects_characters, assert_val=False)
    print("Is equal to circle list?")
    _assert_seq(test_objects_characters, test_objects_circle)
    print("Is equal to old version?")
    _assert_seq(test_objects_characters, test_objects_original)

    print("\n____\nWhat if we return self from a method?\n")
    self_list_protected = [obj.self_method() for obj in test_objects_characters]
    print("'self' is automatically converted to the queen for consistency!")
    print("Are they unique objects?")
    _assert_seq(self_list_protected, assert_val=False)
    print("Does it still evaluate as the same as the previous characters list?")
    _assert_seq(self_list_protected, test_objects_characters)
    print("\nLet's try converting to a class with a @resist decorated method returning 'self'.\n____\n")

    print("To Punctuation-")
    test_objects_punctuation = _convert_seq(test_objects_characters, _Punctuation)
    print("Are they unique objects?")
    _assert_seq(test_objects_punctuation, assert_val=False)
    print("Is equal to character list?")
    _assert_seq(test_objects_punctuation, test_objects_characters)
    print("Is equal to circle list?")
    _assert_seq(test_objects_punctuation, test_objects_circle)
    print("Is equal to old version?")
    _assert_seq(test_objects_punctuation, test_objects_original)

    print("\n____\nWhat if we return self from a method decorated with @resist?\n")
    self_list_unprotected = [obj.self_method() for obj in test_objects_punctuation]
    print("A method decorated with @resist will not convert 'self' to the queen reference. (not suggested)")
    print("Are they unique objects?")
    _assert_seq(self_list_unprotected, assert_val=False)
    print("Do they no longer evaluate as the same object from the previous punctuation list?")
    _assert_seq(self_list_unprotected, test_objects_punctuation, assert_val=False)
    print("\nWhat if we retrieve the drones from the previous characters list?")
    drone_list_characters = [obj.drone for obj in test_objects_characters]
    print("Does it evaluate as the same to the @resist self list?")
    _assert_seq(drone_list_characters, self_list_unprotected)
    print("\nWhat if we retrieve the queen from the @resist self list?")
    self_list_restored = [obj.queen for obj in self_list_unprotected]
    print("Does it evaluate as the same to the original characters list?")
    _assert_seq(self_list_restored, test_objects_characters)
    print("\nTests Complete\n____")


if __name__ == "__main__":
    main()
