# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements. See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership. The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License. You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the License for the
# specific language governing permissions and limitations
# under the License.

from __future__ import annotations

from dataclasses import dataclass
from typing import *

from .result import Result

# Heavily inpspired by functional parsers:
#   https://github.com/dasch/parser/blob/3.0.0/src/Parser.elm
#   https://github.com/elm/parser/blob/1.1.0/src/Parser.elm

a = TypeVar('a')
b = TypeVar('b')


#===--- State ---===#

@dataclass
class State:
    """ The state of a parsing process.

        type State = (
            text: Text
            position: UInt
            row : UInt
            col : UInt
            context : Text
        )
    """
    text: str
    position: int
    row: int
    col: int
    context: str

    def _with(self, text: Optional[str] = None, position: Optional[int] = None, row: Optional[int] = None, col: Optional[int] = None, context: Optional[str] = None) -> State:
        return State(
            text=self.text if text is None else text,
            position=self.position if position is None else position,
            row=self.row if row is None else row,
            col=self.col if col is None else col,
            context=self.context if context is None else context)

    def _currentCharacter(self) -> str:
        return self.text[self.position]

    def _advance(self, n: int = 1) -> State:
        ch = self._currentCharacter()
        return (
            self._with(
                position=self.position + n,
                col=self.col + 1)
            if ch != '\n'
            else self._with(
                position=self.position + n,
                col=1,
                row=self.row + 1))


@dataclass
class let(Generic[a]):
    value: a

    def then(self, expr: Callable[[a], b]) -> b:
        return expr(self.value)


#===--- Error ---===#

@dataclass
class SyntaxError:
    """ Describes an error during parsing.

    Gives more details on what caused a parser to fail,
    and at what position into the input text it failed.

        type SyntaxError = (
            message : Text
            context : Context
        )
    """
    message: str
    state: State


#===--- Parser ---===#

@dataclass
class Parser(Generic[a]):
    """ A parser takes some input text and turns it into a value.

    A `Parser a` is an instruction for how to take some input text and turn
    it into an `a` value.
    """

    def __init__(self, run: Callable[[State], Result[Tuple[a, State], SyntaxError]]) -> None:
        """ type Parser a = (State -> Result (State, a) SyntaxError) """
        self._run_fn = run

    def _run(self, state: State) -> Result[Tuple[a, State], SyntaxError]:
        return self._run_fn(state)

    @staticmethod
    def char(ch: str) -> Parser[str]:
        """ Matches a specific character.

            char : Character -> Parser Character
            char ch =
                Parser <| state ->
                    let gotCh = _currentCharacter state
                    if gotCh == ch
                    then Ok (ch, _advance state)
                    else Error SyntaxError (
                        message = "expected character '$ch', but got '$gotCh'"
                        context = state.context)

            parse 'hello' (char 'h') == Ok 'h'
        """
        if len(ch) != 1:
            raise ValueError(
                f'char accepts only single character strings, got: {repr(ch)}')
        return Parser(lambda state:
                      let(state._currentCharacter())
                      .then(lambda gotCh:
                            Result.Ok((ch, state._advance())) if gotCh == ch
                            else Result.Error(SyntaxError(
                                f"expected character '{ch}', but got '{gotCh}'", state))))

    def parse(self, text: str) -> Result[a, SyntaxError]:
        """ Parse an input text using a specific parser.

        Returns a result containing either the parsed value or an error.

            parse : (Parser a) Text -> Result a SyntaxError
            parse parser text =
                let initialState = State text 0 1 1 ''
                _run parser initialState
                    |> Result.map ((x, _) -> x)

            parse 'xyz' (char 'x') == Ok 'x'
            parse 'xyz' (char 'w') == Error (message = "expected char 'w', got 'x'", context = (row = 1, col = 1, context = 'character'))
        """
        initialState = State(text, 0, 1, 1, '')
        return self._run(initialState)


#===--- Core ---===#

#===--- Matching ext ---===#

#===--- Matching patterns ---===#

#===--- Matching sequences ---===#

#===--- Chaining parsers ---===#

#===--- Pipelines ---===#

#===--- Transformations ---===#

# {-| A parser that always succeeds with a specified value without reading any input.
#     parse "xyz" (succeed 42) -- Ok 42
# -}
# succeed : a -> Parser a
# succeed val =
#     Parser <|
#         \state ->
#             Ok ( state, val )


# {-| A parser that always fails with a specified error message without reading any
# input.
#     parse "xyz" (fail "nope") -- Err { message = "nope", position = 0 }
# -}
# fail : String -> Parser a
# fail str =
#     Parser <|
#         \(State state) ->
#             Err { message = str, position = state.position, context = state.context }


# {-| Sets the context of the parser. Useful for providing better error messages.
# -}
# inContext : String -> Parser a -> Parser a
# inContext context parser =
#     Parser <|
#         \(State state) ->
#             run parser (State { state | context = Just context })


# {-| In order to support self-referential parsers, you need to introduce lazy
# evaluation.
#     type Tree = Leaf | Node Tree Tree
#     tree : Parser Tree
#     tree =
#         oneOf [ leaf, node ]
#     leaf : Parser Tree
#     leaf =
#         map (always Leaf) (char 'x')
#     node : Parser Tree
#     node =
#         into Node
#             |> ignore (char '@')
#             |> grab (lazy (\_ -> tree))
#             |> grab (lazy (\_ -> tree))
#     parse "x" tree -- Ok Leaf
#     parse "@x@xx" tree -- Ok (Node Leaf (Node Leaf Leaf))
# Without `lazy`, this example would fail due to a circular reference.
# -}
# lazy : (() -> Parser a) -> Parser a
# lazy f =
#     Parser <|
#         \state ->
#             let
#                 (Parser parser) =
#                     f ()
#             in
#             parser state


# {-| Use the specified error message when the parser fails.
#     string "</div>"
#         |> withError "expected closing tag"
# -}
# withError : String -> Parser a -> Parser a
# withError msg parser =
#     Parser <|
#         \state ->
#             run parser state
#                 |> Result.mapError (\err -> { err | message = msg })


# {-| Create a parser that depends on the previous parser's result.
# For example, you can support two different versions of a format if there's
# a version number included:
#     spec : Parser Spec
#     spec =
#         let
#             specByVersion version =
#                 case version of
#                     1 ->
#                         v1
#                     -- assume v1 is a Parser Spec
#                     2 ->
#                         v2
#                     -- assume v2 is a Parser Spec
#                     x ->
#                         fail ("unknown spec version " ++ String.fromInt x)
#         in
#         string "version="
#             |> followedBy int
#             |> andThen specByVersion
# -}
# andThen : (a -> Parser b) -> Parser a -> Parser b
# andThen next parser =
#     Parser <|
#         \state ->
#             run parser state
#                 |> Result.andThen
#                     (\( newState, val ) -> run (next val) newState)


# {-| Create a parser that depends on a previous parser succeeding. Unlike
# [`andThen`](#andThen), this does not preserve the value of the first parser,
# so it's only useful when you want to discard that value.
#     atMention : Parser String
#     atMention =
#         char '@'
#             |> followedBy username
# -}
# followedBy : Parser a -> Parser b -> Parser a
# followedBy kept ignored =
#     ignored
#         |> andThen (\_ -> kept)


# {-| Create a fallback for when a parser fails.
# -}
# orElse : Parser a -> Parser a -> Parser a
# orElse fallback parser =
#     Parser <|
#         \state ->
#             case run parser state of
#                 (Ok _) as result ->
#                     result

#                 Err _ ->
#                     run fallback state


# {-| Map the value of a parser.
#     map (\x -> x * x) int
# -}
# map : (a -> b) -> Parser a -> Parser b
# map f parser =
#     parser
#         |> andThen (\x -> succeed (f x))


# {-| Matches two parsers and combines the result.
#     map2 (\x y -> (x, y)) anyChar anyChar
#         |> parse "xy" -- Ok ('x', 'y')
# -}
# map2 : (a -> b -> c) -> Parser a -> Parser b -> Parser c
# map2 f p1 p2 =
#     p1
#         |> andThen
#             (\x ->
#                 p2
#                     |> andThen (\y -> succeed (f x y))
#             )


# {-| Start a parser pipeline that feeds values into a function.
# Typically used to build up complex values.
#     type Operation = Binary Int Char Int
#     operation : Parser Operation
#     operation =
#         into Operation
#             |> grab int
#             |> ignore blanks
#             |> grab (oneOf [ char '+', char '-', char '*' ])
#             |> ignore blanks
#             |> grab int
#     parse "42 * 13" operation -- Binary 42 '*' 13
# Here we feed three values into `Operation` while ignoring blank characters between
# the values.
# -}
# into : (a -> b) -> Parser (a -> b)
# into =
#     succeed


# {-| Grabs a value and feeds it into a function in a pipeline.
# See [`into`](#into).
# -}
# grab : Parser a -> Parser (a -> b) -> Parser b
# grab next =
#     andThen
#         (\f ->
#             next
#                 |> andThen (\x -> succeed (f x))
#         )


# {-| Ignores a matched value, preserving the previous value in a pipeline.
# See [`into`](#into).
# -}
# ignore : Parser a -> Parser b -> Parser b
# ignore next =
#     andThen
#         (\b ->
#             next
#                 |> followedBy (succeed b)
#         )


# {-| Maybe match a value. If the parser succeeds with `x`, we'll succeed with
# `Just x`. If if fails, we'll succeed with `Nothing`.
#     parse "42" (maybe int) -- Just 42
#     parse "hello" (maybe int) -- Nothing
# -}
# maybe : Parser a -> Parser (Maybe a)
# maybe parser =
#     parser
#         |> map Just
#         |> orElse (succeed Nothing)


# {-| Matches zero or more successive occurrences of a value. Succeeds with
# an empty list if there are no occurrences.
#     parse "xxy" (zeroOrMore (char 'x')) -- Ok [ 'x', 'x' ]
#     parse "yyy" (zeroOrMore (char 'x')) -- Ok []
# -}
# zeroOrMore : Parser a -> Parser (List a)
# zeroOrMore parser =
#     map2 (::) parser (lazy (\_ -> zeroOrMore parser))
#         |> orElse (succeed [])


# {-| Matches one or more successive occurrences of a value. Fails if
# there are no occurrences.
#     parse "xxy" (oneOrMore (char 'x')) -- Ok [ 'x', 'x' ]
#     parse "yyy" (oneOrMore (char 'x')) -- Err { message = "expected char `x`", position = 0 }
# -}
# oneOrMore : Parser a -> Parser (List a)
# oneOrMore parser =
#     map2 (::) parser (zeroOrMore parser)


# {-| Matches a sequence of parsers in turn, succeeding with a list of
# their values if they _all_ succeed.
#     parse "helloworld" (sequence [ string "hello", string "world" ]) -- Ok [ "hello", "world" ]
# -}
# sequence : List (Parser a) -> Parser (List a)
# sequence parsers =
#     case parsers of
#         [] ->
#             succeed []

#         parser :: rest ->
#             map2 (::) parser (sequence rest)


# {-| Matches a specific number of occurrences of a parser, succeeding with a list
# of values.
#     parse "xxxx" (repeat 3 (char 'x')) -- Ok [ 'x', 'x', 'x' ]
# -}
# repeat : Int -> Parser a -> Parser (List a)
# repeat n parser =
#     sequence (List.repeat n parser)


# {-| Matches one of a list of parsers.
#     parse "y" (oneOf [ char 'x', char 'y' ]) -- Ok 'y'
# -}
# oneOf : List (Parser a) -> Parser a
# oneOf parsers =
#     List.foldl orElse (fail "") parsers
#         |> withError "expected one of the parsers to match"


# advance : Int -> State -> State
# advance length (State state) =
#     State
#         { state
#             | position = state.position + length
#             , remaining = List.drop length state.remaining
#         }


# {-| Matches zero or more values until a "stop" parser matches.
#     char '['
#         |> followedBy (until (char ']') anyChar)
#         |> parse "[abc]" -- Ok [ 'a', 'b', 'c' ]
# -}
# until : Parser a -> Parser b -> Parser (List b)
# until stop parser =
#     Parser <|
#         \state ->
#             let
#                 follow =
#                     parser
#                         |> andThen
#                             (\x ->
#                                 until stop parser
#                                     |> map (\xs -> x :: xs)
#                             )
#             in
#             case run stop state of
#                 Ok _ ->
#                     Ok ( state, [] )

#                 Err _ ->
#                     run follow state


# {-| Matches zero or more values separated by a specified parser.
#     separatedBy (char ',') int
#         |> parse "42,13,99" -- Ok [ 42, 13, 99 ]
# -}
# separatedBy : Parser s -> Parser a -> Parser (List a)
# separatedBy separator parser =
#     let
#         empty =
#             succeed []

#         oneElement =
#             parser
#                 |> map List.singleton

#         multipleElements =
#             succeed (::)
#                 |> grab parser
#                 |> ignore separator
#                 |> grab (lazy (\_ -> separatedBy separator parser))
#     in
#     oneOf [ multipleElements, oneElement, empty ]


# {-| Matches the end of the input.
#     char 'x'
#         |> followedBy end
#         |> parse "x" -- Ok ()
# -}
# end : Parser ()
# end =
#     Parser <|
#         \(State state) ->
#             if state.remaining == [] then
#                 Ok ( State state, () )

#             else
#                 Err { message = "expected end", position = state.position, context = state.context }


# {-| Matches any character.
# -}
# anyChar : Parser Char
# anyChar =
#     Parser <|
#         \(State state) ->
#             List.head state.remaining
#                 |> Maybe.map (\chr -> ( advance 1 (State state), chr ))
#                 |> Result.fromMaybe { message = "expected any char", position = state.position, context = state.context }


# {-| Matches a character if some predicate holds.
#     parse "123" (when Char.isDigit) -- Ok '1'
# -}
# when : (Char -> Bool) -> Parser Char
# when predicate =
#     anyChar
#         |> andThen
#             (\c ->
#                 if predicate c then
#                     succeed c

#                 else
#                     fail "failed predicate"
#             )


# {-| Matches a character if the specified parser _fails_.
#     parse "xyz" (except (char 'a')) -- Ok 'x'
#     parse "xyz" (except (char 'x')) -- Err { message = "expected to not match", ... }
# -}
# except : Parser Char -> Parser Char
# except parser =
#     Parser <|
#         \state ->
#             case run parser state of
#                 Ok _ ->
#                     run (fail "expected to not match") state

#                 Err _ ->
#                     run anyChar state


# {-| Turns a parser that returns a list of characters into a parser that
# returns a String.
#     parse "xyz" (stringWith (sequence [ char 'x', anyChar, char 'z' ])) -- Ok "xyz"
# -}
# stringWith : Parser (List Char) -> Parser String
# stringWith =
#     map String.fromList


# {-| Maps a parser to include all the matched input as a String.
#     matchedString (sequence [ word, string "@", word ])
#         |> parse "hello@world!" -- Ok "hello@world"
# -}
# matchedString : Parser a -> Parser String
# matchedString parser =
#     Parser <|
#         \(State state) ->
#             case run parser (State state) of
#                 Ok ( State newState, _ ) ->
#                     let
#                         str =
#                             String.slice state.position newState.position state.input
#                     in
#                     Ok ( State newState, str )

#                 Err err ->
#                     Err err


# {-| A parser that simply reads a specific number of characters from the
# input.
#     parse "xyz" (chomp 2) -- Ok "xy"
# -}
# chomp : Int -> Parser String
# chomp n =
#     List.repeat n anyChar
#         |> sequence
#         |> map String.fromList


# {-| Matches a specific string.
#     parse "hello world" (string "hello") -- Ok "hello"
# -}
# string : String -> Parser String
# string str =
#     Parser <|
#         let
#             strLength =
#                 String.length str

#             chars =
#                 String.toList str
#         in
#         \((State state) as fullState) ->
#             if List.take strLength state.remaining == chars then
#                 Ok ( advance strLength fullState, str )

#             else
#                 run (fail ("expected string `" ++ str ++ "`")) fullState
# """
