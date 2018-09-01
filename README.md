# borg_pod Python design pattern and module.

The Borg Pod pattern provides an easy method for creating dynamic and decoupled classes. Instead of imposing developer
overhead of linking class implementations, designing a state machine, referring to the correct pointers for the owners
of each attribute / method, and debugging the system - you could just put a wrapper above your classes and be done with
it.

## Get

Clone this repo, or use pip3 install borg_pod

## Use

At the top of your module, be sure to include:

from borg_pod import resist, assimilate, BorgPod

Or, if you adhere to Google standards:

import borg_pod as bp_or_be_oil

You've imported borg_pod's relevant attributes directly like a sane person?  Let's say you have some classes you want
to be able to switch an instance between:

    class SomeClassA(object):

        def __init__(self):
            pass

        def my_method(self):
            print("I AM SOME CLASS A")


    class OtherClassB(object):

        def __init__(self):
            print("HOLD ON, I AIN'T SO QUIET.")

        def my_method(self):
            print("...where am I again?")

        def a_unique_method(self, to_print):
            print(to_print)


All you would do is add the @assimilate decorator above both:


    @my_library.assimilate
    class SomeClassA
    ...


    @my_library.assimilate
    class OtherClassB

    ...


Creating and converting an instance of one would look like:


my_first_unique = SomeClassA()

my_second_unique = SomeClassA()

my_third_unique = OtherClassB()

assert my_first_unique is not my_second_unique and my_third_unique is not my_first_unique

first_b = SomeClassB(my_first_unique)

second_b = SomeClassB(my_second_unique)

third_b = SomeClassB(my_third_unique)

assert (first_b is my_first_unique and second_b is my_second_unique and third_b is my_third_unique
    and first_b is not third_b and first_b is not second_b)

And that's it! More advanced usage involves the @resist decorator, to avoid the self reference injection - but most
devs don't need to worry about that. You can find more thorough documentation inside of the module. Classes with
the @assimilate decorator can be subclassed and can be subclasses of other decorated or non-decorated classes.

## Copyright

borg_pod module by Andrew M. Hogan. (borg_pod &copy; 2018 Hogan Consulting Group)

## License

Licensed under the Apache License.
