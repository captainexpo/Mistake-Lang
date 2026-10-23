# The Mistake Language

The Mistake Language (patent not pending) is an esoteric programming language that was designed to be both annoying to program in and, especially, annoying to implement. The majority of the design for the language was done by [@iamawatermelo](https://www.github.com/iamawatermelo), and the implementation of the interpreter was done by me.

The core features of the language include, but are not limited to:
- A semi-functional paradigm
- Variables and functions are unable include letters of the alphabet
- Dynamic typing
- Classes
- Vulkan Compute Shader API
- Airtable database API
- Keyword localization (keywords are automatically translated into other languages if needed)

Below this section lies comprehensive documentation for the usage, installation, and features of the language.

## Installation

MistakeLang is registered on PyPI. To install it, run:

```bash
pip install mistake-lang
```

Or if you also want Vulkan Compute Shader support

```bash
pip install mistake-lang[vulkan]
```

## Usage

To run a MistakeLang script, use the following command:

```bash
mistake-lang [options] filename
```

### Options

- `-h, --help`: Show the help message and exit.
- `--time`: Print timing information.
- `--tokens`: Print tokens.
- `--ast`: Print the Abstract Syntax Tree (AST).
- `--no-exe`: Do not execute the script.
- `--env ENV`: Path to the `.env` file.
- `--vulkan`: Enable Vulkan support. (Requires Vulkan SDK)
- `--unsafe`: Enable unsafe mode.
- `--end-env`: Print the global environment at the end.
- `--language LANGUAGE`: Language for localization. Localizations are automatically generated using the google translate API and thus require access to the internet. Use `--language purge` to purge all localizations.
- `--env-tree`: Print the environment tree.

### Example

To run a script with Vulkan support and print the AST:

```bash
mistake-lang --vulkan --ast my_script.mistake
```


## Overview

Mistake is an imperative, functional, object-oriented, message-passing language.
Through the use of human language, it is easy to write for beginners.

All language constructs are in the user's language because it makes programs self-documenting and readable. This document is in American English.

### Core data types

These are some core data types:

* `function`
* `string`
* `number`

Users can also create classes.
In Mistake, all numbers are double precision floating point numbers.

## Syntax reference

### Meta-syntax

Note that keywords must be translated to the user's preferred language. In this document, we assume American English.
blah matches blah, but also Blah and bLaH. All keywords are case-insensitive in Mistake.
`[blah]` also matches blah
`[blah]?`  matches blah or nothing
`[blah]...` matches one or more blah s in between spaces
`[blah]?...` matches zero or more blahs in between spaces
`<something>` is a class of character
For the avoidance of doubt, a character is a Unicode grapheme.

### Classes of characters

* `<identifier>` is any character that is not whitespace or in the Latin alphabet (a to z). Identifiers must contain at least one non-numeric character to distinguish them from number literals.
    * `-67.42!` is an identifier.
    * `-67.42` is a number.
    * `67.42.128.6` is an identifier, not an invalid number.
* `<expression>` is, well, an expression.
* `<string>`  is a set of characters. See the specific syntax element for what the string is terminated by.
* `<lifetime>` is a number that ends in s, l or u (meaning seconds, lines and a timestamp respectively).
    * Timestamps are given in milliseconds since Jan 1, 2020 (which is the Mistake epoch).
* Anything else refers to another syntax element.

### Lines

A "line" is one statement in the imperative section.

Comments

Comments end at the end of a line (at a \n).
Comments may exist anywhere. Comment bodies may contain anything.
Comments are simply ignored.

```go
comment <string>
```

### Statements

An entire Mistake file is just a set of statements. A top-level statement is said to be in the "imperative section".

```go
[<statement>]...?
```

#### Expression statements

A statement can be an expression terminated by end. Whatever the expression returns is simply discarded.

```go
<expression> end
```

#### Variable statement

public is only valid in a class statement.

```go
[public] variable <identifier> [lifetime <lifetime>]? [type <string>] is <expression> end
```

#### Jump statements

Note that jump statements are only valid in the imperative section.

```go
jump <expression> of <expression> end
```

### Expressions

#### Functions

```go
[impure] function [<identifier>]... returns <expression> close
```

#### Open blocks

```go
open [<statement>]...? <expression> close
```

#### Function application

```go
<identifier> <expression>
```

Note that `; 1 2 3 4` is `;(1)(2)(3)(4)`, not `;(1(2(3(4))))`.

#### String expressions

String expressions are terminated with close. This means that string expressions can't have "close" in them.

```go
string <string> close
```

Strings in Mistake can have escape sequences. For familiarity, Mistake uses a familiar syntax for escape sequences:

```go
string Bits &amp; bytes close
```

Note that Mistake strings may contain arbitrary bytes.

```go
string Bits &#0; bytes close
```

#### Match expressions

The output of the match expression is stored in a special variable @.

```go
match <expression> cases [case <expression> then <expression> close]...? otherwise <expression> close
```

#### Class expressions

Class bodies inherit the purity of its environment.

```go
class [inherits <identifier> has]? [<statement>]...? end
```

#### Member expressions

```go
member <identifier> of <identifier>
```

#### New expressions

```go
new <identifier>
```

#### Unit expressions

```go
unit
```

#### Number literal

A number literal is a number like `-6`, `420.68`, or `82`.

### Builtin functions

Functions that don't return anything return unit.

#### Operators

* `+`, `-`, `/`, `*` are math operations.
    * For numbers, they do what you expect.
    * For strings:
        * `+`  joins them together.
        * `-`  does nothing.
        * `/`  divides the string (e.g `/ string Hello close 5`  is "H").
        * `*`  multiplies the string (e.g `* string Hello close 5`  is "HelloHelloHelloHelloHello").
    * For lists, it does the same as strings.
    * For everything else, it does nothing.
* `=`, `≠` are equals and not equals
* `>`, `<`, `≥`, `≤` do what you expect them to:
    * `>`  evaluates to true if its second argument is greater than its first
    * `<`  evaluates to true if its second argument is less than its first
    * `≥`  evaluates to true if its second argument is greater than or equal to its first
    * `≤`  evaluates to true if its second argument is less than or equal to its first
* `->` gets the "length" of something.
    * For strings, it is the length of the string in bytes.
    * For match objects, it is the amount of match groups.
    * For numbers, it is the length of the number printed out in Base 10.
    * For unit, it is 0.
    * For lists, it is the length of the list.
    * For tasks, it is the amount of seconds the task has been running.
    * And so on. For things which don't have an obvious "length", it is 0.
* `??` formats something as a string, like `?!` does.

#### Other functions

* `?!` prints its only argument. Impure.
* `!` creates a mutable box.
    * `!?`  gets the contents of a mutable box.
    * `!<`  sets them. Impure.
* `|>|` pushes its only argument to the stack. Impure.
* `|<|` pops the top of the stack and calls its argument with the value. Where there is no value, the function does nothing. Impure.
* `!!` asserts that a value is truthy (not false or unit). If the value is not truthy, crashes the program.
* `[/]` runs a callback in an amount of seconds. Returns a task object. When killed before the callback has run, the callback is never run. When killed while the callback is running, the callback is killed. Note that Mistake uses decimal seconds.

### Async

*  `=!=` creates a channel.
*  `<<` writes to a channel. Impure.
    * If the argument passed is not a channel, it does nothing.
* `>>` reads from a channel, blocking and returning what it got. Also impure.
    * If the argument passed is not a channel. it returns unit.
* `<!>` runs a new task asynchronously.
* `</>` kills a task.

Networking

All networking functions are impure.

* `<=#=>` creates a TCP server. `<=?=>` creates a UDP server.
    * Servers are task objects and can also be killed. When they are killed, they stop listening on its port and any running callbacks are killed too.
    * `==>#` binds the server to the port set by its argument. Returns true if successful and false otherwise.
    * `==>?` binds the server to the hostname set by its argument. Returns true if successful and false otherwise.
    * `==>!` sets the server's callback.
        * For TCP servers, the server callback is called asynchronously with a TCP socket object. Callbacks may be impure.
        * For UDP servers, the server callback is called asynchronously with a string object containing the message content. Callbacks may be impure.
* `<=#=` creates a TCP socket. `<=?=` creates a UDP socket.
    * If a connection could not be made, returns unit instead.
    * `<<` on a TCP and UDP socket sends a string. Blocking.
        * Returns true if successful and false otherwise.
    * `>|<` closes the socket on both TCP and UDP sockets.
    * `>>` on TCP sockets receives a string. Blocking. On a UDP socket, does nothing.

### Airtable

Mistake is a language for Hack Clubbers. Therefore, it has native Airtable integration for maximum development flow.
All functions except `{!}` are impure and blocking.

* `{!}` creates a base object. A base object can be called to return a table object.
* `{?}` lists records in a table. Returns a list of record object.
* `{>}` fetches a specific record from a table. Returns a record object.
* `{<}` puts a record into a table. Returns the new record object.
* `{\}` modifies a record. Returns the new record object.
* `{-}` deletes a record by its ID.

You can use these functions to work with record objects.

* `{!` creates a new record object.
* `{<` sets a field.
* `{>` gets a field.
* `{#<` sets the record's ID.
* `{#>` gets the record's ID.

You can use these functions to manipulate your schema

* `{{?` gets the schema
* `{{+` creates a field
* `{{=` updates a field

You can use these functions to manipulate bases

* `{}?` lists bases
* `{}??` get base schema
* `{}+` create base [NOT IMPLEMENTED]

### Lists

* `[!]` creates a new list object.
* `[<]` sets an item in a list.
* `[>]` gets an item in a list.

### Regex

* `/?/` creates a new compiled regex, taking a string as the regex source. Returns a compiled regex function or unit if it failed.
* Calling a regex function returns a list of match objects. May have a length of zero if there were no matches.
* `/>?/` gets a capture group.
* `/>"/` gets the entire match as a string.

## The basics of Mistake

### Terminology

The "imperative section" is the top-level of a file. Each statement is evaluated individually, one after the other.
See the syntax reference for details.

### Types

Mistake has a few datatypes:

* number
* string
* boolean
* unit (which is like null/None/undefined/etc)

### Comments

```go
comment Comments terminate with a newline.
sylw Wrth gwrs, gallwch chi siarad eich iaith eich hun os yw'n defnyddio'r wyddor Ladin.
comment The interpreter should check the user's locale.
```
### Functions

To call a function in Mistake, just write the function name and then its parameters.

```go
+ 5 6 end  comment Is 11.
comment +(5)(6)
```
### Variables

```go
variable ?? is 5 end
?! ?? end  comment Prints 5. ?! prints its argument to the console.
```

In Mistake, variables can only be assigned to once.

```go
variable ?1 is 5 end
variable ?1 is 6 end  comment Throws a compilation error.
```

`_` is a special identifier. You can assign to it multiple times:

```go
variable _ is 5 end
variable _ is 6 end
```

However, you can't use it as a normal variable. It discards whatever is written to it.

```go
?! _  comment Throws a compilation error.
```

`@` is also a special identifier. You can't assign to it.

```go
variable @ is 5 end  comment Throws a compilation error.
```

You'll understand what @ is later.

### Open / close statements

Open blocks create a new scope. The last expression in an open block is returned from the block.

```go
variable 5+6 is open
  variable !1 is 5 end

  comment The last thing is returned.
  comment So, the last thing does not have an "end" after it.
  + !1 6
close end

?! 5+6 end
?! !1  comment Throws a compilation error, because ! isn't in this scope!
```

### Function application

In Mistake, all functions are curried.
For example, `+ 5` returns a function that, when called with a number, will add 5 to it and return it.

```go
variable +5 is + 5 end

comment The below prints 11.
?! open +5 6 close end
```

### Strings and string manipulation

For example:

```go
comment The below prints "Hello, world! What a great comment."
?! string Hello, world! What a great comment. close end
```

Note that you can't write "close" in a string.
Luckily, Mistake supports escape sequences.

```go
?! string Please clos&#101; the door. close end
```

You can use other mathematical operations with strings too:

```go
?! open * string Hello close 5 end  comment This print HelloHelloHelloHelloHello
?! open / string Hello close 5 end  comment This prints H
```

### Variable lifetimes

Mistake has lifetimes. You can specify how long a variable lasts in either seconds or lines.

```go
variable ??2 lifetime 20s is 5 end          comment lasts for 20 decimal seconds
variable ??3 lifetime 1l is 5 end           comment lasts for 1 line

comment Lasts until 2069.
comment Timestamps are given in decimal milliseconds relative to the Mistake epoch,
comment which is January 1, 2020.
variable ??4 lifetime 1343656342u is 5 end

comment Trying to access an expired variable crashes the program.
?! ??3 end  comment Crashes - it expired 1 line ago.
```

### Defining new functions

In Mistake, functions are just values.
You can use the function keyword to create one. Here's a function that discards its only parameter and returns 5:

```go
function _ returns 5 close
```

You can write curried functions like this:

```go
function $1 $2 returns 5 close
```

Which is syntactic sugar for:

```go
function $1 returns function $2 returns 5 close close
```

Assign functions to variables to use them again later.

```go
comment JavaScript does this, so it must be good.
comment (*+5) takes two numbers, multiplies them together and adds 5.
variable (*+5) is function ? ! returns + open * ? ! close 5 close end

comment Impure functions must say "impure".
comment Otherwise, they must have no side effects.
comment This is so that the compiler can theoretically apply theoretical optimisations to theoretical functions.
variable ?!(*+5) is impure function ? ! returns ?! open (*+5) close close end
```

### The stack

In order to present a familiar interface to those coming from stack-based languages, Mistake provides a global stack.

```go
comment Trying to get closer to hardware implementations, you are able to use a "stack" to run functions as well.

comment Pushes 5 onto the stack, then 7.
|>| 5 end
|>| 7 end

comment Adds 7 and 5
?! |<| |<| + end

comment Multiplies 5 and the data at the top of the stack
comment As there is no data, the multiplication function will simply not be called in order to soften your mistake
|<| * 5 end
```

Note that the stack may only be used in impure functions.

### Jumps

In Mistake, there are no imports.
However, you can jump to lines of other programs.
Here's a file:

```go
comment This is utils.mistake

variable (&&) is 5 end

comment jump can only be used at the top-level, in the imperative section.
jump $<? of $<" end
```

And another file:

```go
comment This is main.mistake

comment [?] is a function that, when called, returns the current line.
variable $<" is string main.mistake end
variable $<? is + open [?] unit close 2 end
jump 1 of string utils.mistake close end

comment Okay, utils.mistake should've jumped back now.
?! (&&) end  comment Prints 5
```

Jumps may only be used in the imperative section.

Note that different Mistake programs may use different calling conventions.

Lines in Mistake are different to what you may expect them to be.
In Mistake, a "line" is anything that ends in "end". An entire class definition is one "line". A comment is not a line.
For example:

```go
open
  ?! open [?] unit close end comment Prints 1
  ?! open [?] unit close end comment Still prints 1
  ?! open [?] unit close end comment We're still on line 1!
close end
```

Lines start from 1.

### Pattern matching

```go
variable # is 5 end

comment The below prints "# is 5 :)".
?! match # cases
  comment @ is what is being matched on.
  comment Each case statement is evaluated and cast to a boolean.
  comment Note that everything that is not either "false" or "unit" is truthy.

  case = 5 @ then string # is 5 :) close
  otherwise string # is not 5 :( close
close end
```

### Channels and asynchronous programming

Mistake supports asynchronous programming for building Web Scale:tm: applications.
Let's create a channel:

```go
variable [] is =!= end

You can send a message to a channel with <<.

<< [] 5 end
```

However, our message is simply lost. If nothing is listening on the channel, Mistake will just discard the message. Let's write a function to listen to messages on the channel with >>:

```go
variable <[] is function _ open
  variable $ is >> [] end
  ?! $ end
  <[] unit end
close close end
```

If we called this function now, the program would hang forever as `<<` simply waits for a new message indefinitely. Let's instead run this function asynchronously, with `<!>.`

```go
variable ?< is open <!> <[] close end

<!> returns a task object that we can later cancel. Mistake will wait for all tasks to complete before exiting, so if we don't cancel the task it will simply hang forever. If we run the statement from earlier:

<< [] 5 end  comment Prints 5 to the screen!
```

5 will be printed to the screen! Now that our task has served its purpose, we can kill it with </>.

```go
</> ?< end
```

### Typing

Some programmers feel that types make programming easier. Luckily, the built in Mistake type solver can figure out most of your types.

```go
variable ? is + 5 6 end
```

The built-in type solver would infer ? as being a number. You can state this explicitly:

```go
variable ? type number is + 5 6 end
```

However, type hints are just for you. They aren't checked at runtime.

### Mutable boxes

Sometimes you want mutability. That's fine. Use ! to create a mutable box:

```go
variable [] is ! 5 end  comment Creates a mutable box with initial value 5

Use !? and !< to read and write to a mutable box respectively:

?! open !? [] close end  comment Prints 5
!< [] 6 end              comment Sets the box's content to 6
?! open !? [] close end  comment Now prints 6
```

Note that < is impure.

### Classes

Mistake is an enterprise language, which is why it has classes. Here's a simple counter class:

```go
variable #++ is class has
  variable [#] is 0 end

  public variable ++ is impure function $ returns open
    comment I can access my class variables here!

    comment Add $ to the counter:
    < [#] open + open ? [#] close $ close end

    comment And return it:
    ? [#]
  close close end
close end
```

Create a new instance of it with new:

```go
variable [#] is new #++ end  comment We can reuse [#] because class creates a new scope
```

And access members on it with member ... of ...

```go
member ++ of [#] 55 end

?! member [#] of [#] end  comment Can't do this -- isn't public variable
```

Classes can also be subclassed:

```go
variable 5++ is class inherits #++ has
  public variable +5 is impure function _ returns open
    comment Still can access all of #++'s variables
    ++ 5
  close close end
close end
```

### Web Scale™

Mistake supports building highly scalable web applications with green threading.

TCP Server:
```go
variable $^&* is <=#=> unit end

variable &&& is function <% returns open
	variable !*! is function _ returns open
		<< <% string Hello, World!<br> close end
		variable >% is >> <% end
		?! open >"< >% close end
		match >"< >% cases
			case = @ string exit close then >|< <% close
			otherwise !*! unit close
		close end
	close close end
	?! string Callback has run close end
	!*! unit end
close close end

variable #() is 8080 end

==># $^&* #() end
?! open + string Server is running on port:  close open ?? #() close close end
==>! $^&* &&& end
```

UDP Server:
```go
variable <()> is <=?=> unit end

==>? <()> string 127.0.0.1:8080 close end
==>! <()> function %1 returns open ?! %1 close close end

[/] 15 function _ returns </> <()> close end
```

UDP Socket:
```go
variable <()> is <=?= unit end

==>? <()> string 127.0.0.1:8080 close end

<< <()> string Hello World! close end
```

### Lists

To create a list, use `[!]`. `[<]` sets an item of a list, `[>]` gets them. Note that in Mistake, list indexes start from 1 to be more friendly to new developers.

```go
variable [] is [!] unit end

[<] [] 1 5              comment Set the first list item to 1.
?! open [>] [] 1 close  comment Prints "5"
```

### Advanced string manipulation

Mistake supports regex. The `/?/` function can be used to search through a string, and returns a list of match objects.

```go
variable <> is /?/ string /^Hello (\w+)?/ close string Hello, Sarah! close end
?! "" end  comment Prints "list"
```

Use `[>]` to get the nth match of a list, starting from 1.

```go
variable "" is />/ <> 1 end
?! "" end  comment Prints "match"
```

Because there were no more than 1 match, `[>] <> 2` would return unit.
Use `/>"/` to get the string that was matched.

```go
?! open />"/ "" close end  Prints "Hello, Sarah"
```

Use `/>?/` to get a specific capture group, or unit if no such capture group exists or was not matched. Again, starts from 1.

```go
?! open />?/ "" 1 close end  prints "Sarah"
```

### Environment Variables

For the sake of security, mistake supports using .env files to safely store your API keys, passwords, and other sensitive information.

```go
comment This is equivalent to os.environ("THIS_IS_A_KEY") in Python.
[@@@] string THIS_IS_A_KEY close end
```

### Airtable

Mistake supports Airtable to fuel Hack Club's neverending Airtable addiction. See your interpreter's documentation on how to configure Airtable.

```go
comment Create an API instance
{>!<} open [@@@] string AIRTABLE_ACCESS_KEY close close end

comment Create the base object
variable {{}} is {!} open [@@@] string BASE_ID close close end

comment Create the table object
variable ({0}) is {{}} open [@@@] string TABLE_ID close close end

comment Create a dictionary object
variable {1} is {+} unit end

comment Add fields to the dictionary object
comment This will become
comment {
comment 	"Age": 50,
comment 	"Name": "Jake Smith",
comment 	"Email": "person@hackclub.com"
comment }
>{} {1} string Age close 50 end
>{} {1} string Name close string Jake Smith close end
>{} {1} string Email close string person@hackclub.com close end

comment Create the record object
variable <{5}> is {! {1} end

comment Change the name field to 'Bingus Bongus'
{< <{5}> string Name close string Bingus Bongus close end

comment Insert the record into the table
{<} ({0}) <{5}> end

comment Update the name field in the local record to 'Bingus Bongus 2'
{< <{5}> string Name close string Bingus Bongus 2 close end

comment In 2 seconds, update the record on airtable
[/] 2 function _ returns open {\} ({0}) <{5}> close close end

comment In 4 seconds, delete the record on airtable
[/] 4 function _ returns open {-} ({0}) open {#> <{5}> close close close end

comment Get the table schema
?! open {{? ({0}) close end

comment Create a new dictionary
variable ()++ is {+} unit end

comment Add fields to the dictionary
>{} ()++ string color close string greenBright close end
>{} ()++ string icon close string check close end

comment Add a new field to the table schema
variable $$ is {{+ ({0}) string Visited close string checkbox close ()++ end

comment Create a new dictionary
variable (00) is {+} unit end

comment Add fields to the dictionary
>{} (00) string name close string Boo close end
>{} (00) string description close string This is a field, wow! close end

comment In 2 seconds, update the 'Visited' field on the table schema
[/] 2 function _ returns open {{= ({0}) $$ (00) close close end
```

### Advanced functions

We can use the source code of functions to do nifty things! In Mistake, functions are parsed when they are executed, so syntax errors only happen when functions are called.

```go
variable "?" is function _
  blah blah this is invalid syntax blah
close  comment Note that you still need close
```

Note that in function blocks, escape sequences don't work.

```go
variable "!" is function
  Bits &amp; bytes
close
```
Of course, if we try execute that function, we'll get a syntax error.

```go
"!" unit end  comment Syntax error!
```

IMPORTANT: Note that imbalanced open / close blocks are compile-time syntax errors.

```go
variable /// is function
  open
close
```

comment Syntax error - we never closed the function block

### GPGPU

Sometimes, traditional CPUs aren't enough. That's okay. Using Advanced Functions, Mistake now supports GPGPU programming through Vulkan compute shaders.
As a simple example, let's multiply two lists together

All GPGPU functions and constants start with a fire emoji, because it's blazingly fast.

First, let's create the manager object with 🔥🔥. Mistake will handle enabling all of the required extensions and such for you.

```go
variable $$$ is 🔥🔥 end
```

Now, let's create two buffers. First, let's fill both lists with some example values.

```go
comment Create a list for us to turn into a buffer
variable [0] is [!] unit end
[<] [0] 1 1 end
[<] [0] 2 2 end
[<] [0] 3 3 end

comment Create the other list for us to turn into a buffer
variable [1] is [!] unit end
[<] [1] 1 9 end
[<] [1] 2 18 end
[<] [1] 3 27 end
```

Now, let's transfer our buffer over to the GPU.

* `🔥[!]` creates a new buffer.
* `🔥+32` is a datatype constant. It means "unsigned 32 bit integer".

In Mistake, lists don't have to be contiguous. Therefore, the new buffer function will only consider the contiguous part of the array. Like Lua.

```go
variable <#[0] is 🔥[!] 🔥+32 [0] end
variable <#[1] is 🔥[!] 🔥+32 [1] end
```

We also need to make the output buffer that our data will be stored in.

```go
comment Create the output list
variable >[!] is [!] unit end
[<] >[!] 1 0 end
[<] >[!] 2 0 end
[<] >[!] 3 0 end

comment Convert the output list into a compute buffer
variable >#[] is 🔥[!] 🔥+32 >[!] end
```

Okay, we're almost there. Now let's write a simple GPU program with Advanced Functions:

```go
variable 🔥() is function _ returns open
  #version 460

  layout(local_size_x = 1) in;

  layout(set = 0, binding = 0) buffer buf_in_a { uint in_a[]; };
  layout(set = 0, binding = 1) buffer buf_in_b { uint in_b[]; };
  layout(set = 0, binding = 2) buffer buf_out_a { uint out_a[]; };

  void main() {
      uint idx = gl_GlobalInvocationID.x;
      out_a[idx] = in_a[idx] * in_b[idx];
  }
close close end
```

As a final step, we also need to add out input and output buffers to lists in order to run the program.

```go
comment Create the list of input buffers
variable *** is [!] unit end
[<] *** 1 <#[0] end
[<] *** 2 <#[1] end

comment Create the list of output buffers
variable %%% is [!] unit end
[<] %%% 1 >#[] end
```

And now let's execute our program using `🔥🔥()`. Mistake will use sophisticated heuristical detection algorithm systems to determine the optimal workgroup parameters for your program. We also must specify the thread count for the X and Y axies, we'll use (3, 0) because our lists are just 3 elements long.

```go
🔥🔥() 🔥() 3 0 $$$ *** %%% end
```

Our buffer will now contain the data. Simply use 🔥[<] to read the buffer and turn it into a Mistake list, and we're done!

```go
comment Print the result
[/] 1 function _ returns open
?! open 🔥[<] <#[0] close end
?! open 🔥[<] <#[1] close end
?! open 🔥[<] >#[] close
close close end
```

### The use operator

Sometimes, functions want callbacks. This can lead to unreadable code through many layers of nesting. Mistake solves this problem with the use operator.

```go
open
  ?! string Hrm. I'm running synchronously, which isn't Web Scale. close end

  use _ from <!> do
  ?! string Hi, I'm running asynchronously! Woohoo! close end

  use _ from [/] 20 do
  ?! string Woah, it's been 20 seconds! How exciting! close end
close
```

The use operator is syntax sugar for writing a callback. The above program is equal to:

```go
open
  ?! string Hrm. I'm running synchronously, which isn't Web Scale. close end

  <!> function _ returns open
    ?! string Hi, I'm running asynchronously! Woohoo! close end

    [/] 20 function _ returns open
      ?! string woah, it's been 20 seconds! How exciting! close end
    close close end
  close close end
close
```

You can also use use with multiple parameters:

```go
use $1 $2 $3 from [#/=\#] do
```

Which is equivalent in semantics to function $1 $2 $3 returns .

```go
with .. do .. close
```

Sometimes, Mistake's simplistic function call syntax is a bit of a bother. Not to worry. With with statements, function calls are now easier than ever.
Let's rewrite the mutable box example to use with statements:

```go
variable [] is ! 5 end  comment Creates a mutable box with initial value 5

with !? [] do ?! close end  comment Prints 5
!< [] 6 end                 comment Sets the box's content to 6
with !? [] do ?! close end  comment Now prints 6
```

You can chain multiple do's together:

```go
variable ?5 is 5 end
variable ?20 is with ?5
  do + 5
  do + 5
  do + 5
close end
```
Every time, the thing in the with is called with the next do and that becomes the value that is then called with the next do (and on and on).

This means that it is equivalent to

```go
+(+(+(5)(?5)))
```
