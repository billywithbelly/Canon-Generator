import music21
import scamp
import copy
import random
import numpy as np
from music21.scale import Direction

# define some readability constants
SINGLE_NOTE = 0
DOUBLE_NOTE = 1
methods = [SINGLE_NOTE, DOUBLE_NOTE]

ODD_UPPER = True
ODD_LOWER = False

possible_directions = [ Direction.ASCENDING, Direction.DESCENDING ]
jump_intervals = [0, 0]

def pairwise(iterable):
    """
    takes a list and returns a new list containing the elements pairwise
    with overlap

    s -> (s[0], s[1]), (s[1], s[2]), (s[2], s[3]), ..., (s[Last], None)
    """
    return list(zip(iterable, iterable[1:])) + [(iterable[-1], None)]


def median(lst, if_even_length_use_upper_element=False):
    """ return the median of a list """
    length = len(lst)

    if length == 0:
        return None

    if length == 1:
        return lst[0]

    if length % 2 != 0:
        # median of a list with odd lenght is well-defined
        return lst[(length - 1) // 2]
    else:
        # median of a list with even length is a bit tricky
        if not if_even_length_use_upper_element:
            return lst[(length - 1) // 2]
        else:
            return lst[(length) // 2]


def realize_chord(chordstring, numofpitch=5, baseoctave=4, direction="ascending"):
    """
    given a chordstring like Am7, return a list of numofpitch pitches, starting in octave baseoctave, and ascending
    if direction == "descending", reverse the list of pitches before returning them
    """

    pitches = music21.harmony.ChordSymbol(chordstring).pitches
    num_iter = numofpitch // len(pitches) + 1
    octave_correction = baseoctave - pitches[0].octave
    result = []
    actual_pitches = 0
    for i in range(num_iter):
        for p in pitches:
            if actual_pitches < numofpitch:
                newp = copy.deepcopy(p)
                newp.octave = newp.octave + octave_correction
                result.append(newp)
                actual_pitches += 1
            else:
                if direction == "ascending":
                    return result
                else:
                    result.reverse()
                    return result
        octave_correction += 1

    if direction == "ascending":
        return result
    else:
        result.reverse()
        return result


class Identity(object):
    """
    transformation that transforms a note into itself
    when selecting transformations at random, it is
    useful to have some identity transformations taking
    place in order not to make the score too busy
    """

    def __init__(self):
        pass

    def transform(self, scale, note, note2=None):
        new_stream = music21.stream.Stream()
        new_note = copy.deepcopy(note)
        # chosen_interval = random.choice(jump_intervals)
        # interval = music21.interval.Interval(chosen_interval)
        # next_pitch = interval.transposePitch(new_note.pitch)    
        # new_note.pitch = next_pitch
        new_stream.append(new_note)
        return new_stream


class OneToThree(object):
    """
    transformation that randomly transforms one note into three notes
    * total duration is kept
    * first note and last note equal the original note
    * middle note is the neighbour note
    """

    def __init__(self):
        pass

    def transform(self, scale, note):
        new_note = copy.deepcopy(note)
        if new_note.isRest:
            new_stream = music21.stream.Stream()
            new_stream.append(new_note)
            return new_stream

        possible_duration = [
            [0.5, 0.25, 0.25]
            ]
        
        chosen_dur = random.choice(possible_duration)
        random.shuffle(chosen_dur)
        chosen_step = random.choice(possible_directions)

        new_note.quarterLength = chosen_dur[0] * note.quarterLength
        new_stream = music21.stream.Stream()

        new_stream.append(new_note)

        new_note2 = music21.note.Note()
        # chosen_interval = random.choice(jump_intervals)
        # interval = music21.interval.Interval(chosen_interval)
        next_pitch = scale.next(new_note.pitch, direction=chosen_step)
        next_pitch = next_pitch

        new_note2.pitch = next_pitch
        new_note2.quarterLength = chosen_dur[1] * note.quarterLength
        new_stream.append(new_note2)

        new_note3 = copy.deepcopy(new_note)
        new_note3.quarterLength = chosen_dur[2] * note.quarterLength
        chosen_interval = random.choice(jump_intervals)
        interval = music21.interval.Interval(chosen_interval)
        new_note3 = interval.transposeNote(new_note3)
        new_stream.append(new_note3)
        return new_stream


class TwoToThree(object):
    """
    transformation that looks at current and next note,
    and interpolates a note in between (a generalization of the concept
    of a "passing" note)

    total duration doesn't change: duration of current note is
    spread over a copy of the current note and an interpolated note
    """

    def __init__(self):
        pass

    def transform(self, scale, note1, note2):
        new_note = copy.deepcopy(note1)

        if note2 is None:
            stream = music21.stream.Stream()
            stream.insert(0, new_note)
            return stream

        if new_note.isRest:
            new_stream = music21.stream.Stream()
            new_stream.append(new_note)
            return new_stream

        pitches = scale.getPitches(new_note.pitch, note2.pitch)
        rounding_strategy = random.choice([ODD_UPPER, ODD_LOWER])

        possible_durations = [
            [0.5, 0.5],
            [0.75, 0.25],
        ]

        chosen_dur = random.choice(possible_durations)
        random.shuffle(chosen_dur)

        new_note.quarterLength = chosen_dur[0] * note1.quarterLength
        new_stream = music21.stream.Stream()
        chosen_interval = random.choice(jump_intervals)
        interval = music21.interval.Interval(chosen_interval)
        new_stream.append(interval.transposeNote(new_note))

        new_note2 = copy.deepcopy(new_note)
        new_note2.pitch = median(pitches, rounding_strategy)
        new_note2.quarterLength = chosen_dur[1] * note1.quarterLength
        # chosen_interval = random.choice(jump_intervals)
        # interval = music21.interval.Interval(chosen_interval)
        # new_stream.append(interval.transposeNote(new_note2))
        new_stream.append(new_note2)

        return new_stream


class TwoToFour(object):
    def __init__(self):
        pass

    def transform(self, scale, note1, note2):
        new_note = copy.deepcopy(note1)

        if note2 is None:
            stream = music21.stream.Stream()
            stream.insert(0, new_note)
            return stream

        if new_note.isRest:
            new_stream = music21.stream.Stream()
            new_stream.append(new_note)
            return new_stream

        possible_durations = [
            [0.25, 0.25, 0.5],
            [0.25, 0.375, 0.375],
        ]
        chosen_dur = random.choice(possible_durations)
        random.shuffle(chosen_dur)

        chosen_direction = random.choice(possible_directions)
        other_direction = list(set(possible_directions) - set([chosen_direction]))[0]

        new_note.quarterLength = chosen_dur[0] * note1.quarterLength
        new_stream = music21.stream.Stream()
        chosen_interval = random.choice(jump_intervals)
        interval = music21.interval.Interval(chosen_interval)
        new_stream.append(interval.transposeNote(new_note))

        new_note2 = copy.deepcopy(note2)
        new_note2.pitch = scale.next(note2.pitch, direction=chosen_direction)
        new_note2.quarterLength = chosen_dur[1] * note1.quarterLength
        chosen_interval = random.choice(jump_intervals)
        interval = music21.interval.Interval(chosen_interval)
        new_stream.append(interval.transposeNote(new_note2))

        new_note3 = copy.deepcopy(note2)
        new_note3.pitch = scale.next(note2.pitch, direction=other_direction)
        new_note3.quarterLength = chosen_dur[2] * note1.quarterLength
        chosen_interval = random.choice(jump_intervals)
        interval = music21.interval.Interval(chosen_interval)
        new_stream.append(interval.transposeNote(new_note3))

        return new_stream


class OneToFour(object):
    """
    Transformation that expands one note into four notes.
    * Total duration is kept.
    * First and last notes equal the original note.
    * Middle two notes are neighboring notes in the scale.
    """

    def __init__(self):
        pass

    def transform(self, scale, note):
        new_note = copy.deepcopy(note)

        if new_note.isRest:
            new_stream = music21.stream.Stream()
            new_stream.append(new_note)
            return new_stream

        possible_durations = [
            [0.25, 0.25, 0.25, 0.25],
            [0.25, 0.125, 0.25, 0.375],
        ]

        chosen_dur = random.choice(possible_durations)
        chosen_step = random.choice(possible_directions)

        new_note.quarterLength = chosen_dur[0] * note.quarterLength
        new_stream = music21.stream.Stream()

        new_stream.append(new_note)

        new_note2 = music21.note.Note()
        next_pitch = scale.next(new_note.pitch, direction=chosen_step)
        new_note2.pitch = next_pitch
        new_note2.quarterLength = chosen_dur[1] * note.quarterLength
        chosen_interval = random.choice(jump_intervals)
        interval = music21.interval.Interval(chosen_interval)
        new_stream.append(interval.transposeNote(new_note2))

        new_note3 = copy.deepcopy(new_note)
        new_note3.quarterLength = chosen_dur[2] * note.quarterLength
        chosen_interval = random.choice(jump_intervals)
        interval = music21.interval.Interval(chosen_interval)
        new_stream.append(interval.transposeNote(new_note3))

        new_note4 = copy.deepcopy(new_note)
        new_note4.quarterLength = chosen_dur[3] * note.quarterLength
        chosen_interval = random.choice(jump_intervals)
        interval = music21.interval.Interval(chosen_interval)
        new_stream.append(interval.transposeNote(new_note4))

        return new_stream

# list of transformations that transform a single note to a series of new notes
# identity is listed more than once to increase the chance of it getting chosen
single_note_transformers = [Identity,
                            Identity,
                            Identity,
                            OneToThree,
                            OneToThree,
                            OneToFour,
                            ]

# list of transformations that transform a single note based on both current and next note
# idenity is listed more than once to give it more chance of being chosen
double_note_transformers = [Identity,
                            Identity,
                            Identity,
                            Identity,
                            TwoToThree,
                            TwoToThree,
                            TwoToFour,
                            TwoToFour,
                            ]


def spiceup_streams(streams, scale, repetitions=1):
    """
    function that takes a stream of parts
    and spices up every part using the
    Identity, OneToThree, TwoToThree, TwoToFour, ...
    transformations

    * it requires a scale in which to interpret the streams
    * it can create "repetitions" spiced sequences of the given stream
    """
    newtotalstream = music21.stream.Stream()
    for i, part in enumerate(streams):
        newstream = music21.stream.Stream()
        for x in range(repetitions):
            for note, nextnote in pairwise(part.notesAndRests):
                new_note = copy.deepcopy(note)
                new_nextnote = copy.deepcopy(nextnote)
                method = random.choice(methods)
                if (i == 0):
                    trafo = Identity()
                    newstream.append(trafo.transform(scale, new_note).flat.elements)
                elif (i == 1):
                    trafo = TwoToThree()
                    newstream.append(trafo.transform(scale, new_note, new_nextnote).flat.elements)
                elif (i == 2):
                    trafo = OneToThree()
                    newstream.append(trafo.transform(scale, new_note).flat.elements)
                else: 
                    if method == SINGLE_NOTE:
                        trafo = random.choice(single_note_transformers)()
                        newstream.append(trafo.transform(scale, new_note).flat.elements)
                    elif method == DOUBLE_NOTE:
                        trafo = random.choice(double_note_transformers)()
                        newstream.append(trafo.transform(scale, new_note, new_nextnote).flat.elements)
        newtotalstream.insert(0, newstream)
    return newtotalstream


def serialize_stream(stream, repeats=1):
    """
    function that takes a stream of parallel parts
    and returns a stream with all parts sequenced one after the other.
    Basically create the delays between voices
    """
    new_stream = music21.stream.Stream()
    copies = len(stream)
    for i in range(copies):
        for part in stream:
            length = part.duration.quarterLength
            new_stream.append(copy.deepcopy(part.flat.elements))
    return new_stream, length

def notate_voice(part, initial_rest, notesandrests):
    if initial_rest:
        scamp.wait(initial_rest)
    NOTE = type(music21.note.Note())
    REST = type(music21.note.Rest())
    for event in notesandrests:
        if type(event) == NOTE:
            part.play_note(event.pitch.midi, 0.7, event.quarterLength)
        elif type(event) == REST:
            scamp.wait(event.quarterLength)


def canon(serialized_stream, delay, base_ser, instruments, voices, extra_transposition_map, tempo=120):
    """
    function that takes serialized stream and sequences it against
    itself voices times with a delay "delay"
    """
    s = scamp.Session(tempo=tempo)
    s.fast_forward_in_beats(10000)
    parts = [s.new_part(instruments[i]) for i in range(len(instruments))]
    s.start_transcribing()
    initial_rests = [(i+1) * delay for i in range(voices)]

    for v in range(voices):
        interval = extra_transposition_map[v]
        scamp.fork(notate_voice, args=(
            parts[v], initial_rests[v], copy.deepcopy(serialized_stream).transpose(interval).flat.notesAndRests))
    
    
    scamp.fork(notate_voice, args=(
            parts[len(instruments)-1], 0, copy.deepcopy(base_ser).transpose(interval).flat.notesAndRests))
    s.wait_for_children_to_finish()

    performance = s.stop_transcribing()
    return performance


if __name__ == "__main__":
    ############################################################################
    #
    # START OF USER EDITABLE CODE
    #
    ############################################################################
    # define a chord progression that serves as basis for the canon (change this!)
    path_to_musescore = ''  # change as needed; leave empty to use default settings
    
    
    chords = "C G Am Em F C F G"
    # scale in which to interpret these chords
    scale = music21.scale.MajorScale("C")
    
    
    # create list of instruments to use
    instruments = ['violin', 'violin', 'violin', 'viola', 'viola', 'cello']
    voices = len(instruments)-1 # The last instrument is the base instrument
     # define extra transpositions for different voices (e.g. +12, -24, ...)
    # note that the currently implemented method only gives good results with multiples of 12
    voice_transpositions = [0, 0, -12, -24, -24, -36]

    # realize the chords in base octave 4 (e.g. 4)
    octave = 4
    # realize the chords using half notes (e.g. 1 for a whole note)
    quarterLength = 2 # 1 for 2 measures
    # number of times to spice-up the streams (e.g. 2)
    spice_depth = 1
    # how many instances of the same chords to stack (e.g. 2)
    stacking = 1
   
    ############################################################################
    #
    # END OF USER EDITABLE CODE
    #
    ############################################################################

    # prepare some streams: one per voice
    # all bass notes of each chord form one voice
    # all 2nd notes of each chord form a second voice
    # ...
    # convert chords to notes and stuff into a stream
    streams = {}
    base_streams = {}
    splitted_chords = chords.split(" ")
    for v in range(voices):
        streams[v] = music21.stream.Stream()
    base_streams[0] = music21.stream.Stream()
    # split each chord into a separate voice
    for c in splitted_chords:
        pitches = realize_chord(c, voices, octave, direction=possible_directions[1])
        for v in range(voices):
            note = music21.note.Note(pitches[v])
            note.quarterLength = quarterLength
            streams[v].append(note)
        base_note = music21.note.Note(pitches[v])
        base_note.quarterLength = quarterLength
        base_streams[0].append(base_note)
            
    # combine all voices to one big stream
    totalstream = music21.stream.Stream()
    basestream = music21.stream.Stream()
    for r in range(stacking):
        for s in streams:
            totalstream.insert(0, copy.deepcopy(streams[s]))
            basestream.insert(0, copy.deepcopy(base_streams[0]))
    for s in basestream:
        s[0].pitch = s[0].pitch.transpose(12)
    # add some spice to the boring chords. sugar and spice is always nice
    spiced_streams = [totalstream]
    base_stream = [basestream]
    for s in range(spice_depth):
        # each iteration spices up the stream that was already spiced up in the previous iteration,
        # leading to spicier and spicier streams
        spiced_streams.append(spiceup_streams(spiced_streams[s], scale))

    # debug code: visualize the spiced up chords, and allow the user to abort
    # canon generation if the result is too horrible
    if path_to_musescore:
        music21.environment.set('musicxmlPath', path_to_musescore)
    spiced_streams[-1].show("musicxml")
    
    ser, delay = serialize_stream(spiced_streams[-1])
    base_ser, base_delay = serialize_stream(base_stream[-1])

    # and turn it into a canon. Add extra transpositions to some voices to create some diversity
    canonized = canon(ser, delay, base_ser, instruments, voices * stacking, voice_transpositions)

    # show the final product
    canonized.to_score(title="Canon", composer="canon-gen.py", max_divisor=16).show_xml()
