import ctypes
import os
from ctypes import Structure, c_byte, c_int, c_float, c_bool, c_char_p, POINTER, byref

fti_osc_lib = ctypes.CDLL(os.path.join(os.path.dirname(__file__), "res", "fti_osc.dll"))


# Define the equivalent Python structures to match the C# structs
class OscValueType(ctypes.c_byte):
    _fields_ = [("value", ctypes.c_byte)]


class OscValue(Structure):
    _fields_ = [
        ("Type", OscValueType),
        ("IntValue", c_int),
        ("FloatValue", c_float),
        ("BoolValue", c_bool),
        ("StringValue", c_char_p),
    ]


class OscMessageMeta(Structure):
    _fields_ = [
        ("Address", c_char_p),  # String
        ("ValueLength", c_int),  # usize
        ("Value", ctypes.c_void_p),  # Box<[OscValue]>
    ]


# Define the function prototypes using ctypes
fti_osc_lib.parse_osc.argtypes = [ctypes.POINTER(c_byte), c_int, ctypes.POINTER(c_int), ctypes.POINTER(OscMessageMeta)]
fti_osc_lib.parse_osc.restype = ctypes.c_bool

fti_osc_lib.create_osc_message.argtypes = [ctypes.POINTER(c_byte), ctypes.POINTER(OscMessageMeta)]
fti_osc_lib.create_osc_message.restype = c_int

fti_osc_lib.create_osc_bundle.argtypes = [ctypes.POINTER(c_byte), POINTER(OscMessageMeta), c_int, POINTER(c_int)]
fti_osc_lib.create_osc_bundle.restype = c_int


# Now you can call your Rust functions from Python
def parse_osc(buffer, buffer_length, message_index, message):
    return fti_osc_lib.parse_osc(buffer, buffer_length, message_index, message)


def create_osc_message(buf, osc_template):
    return fti_osc_lib.create_osc_message(buf, osc_template)


def create_osc_bundle(buf, messages, len, message_index):
    return fti_osc_lib.create_osc_bundle(buf, messages, len, message_index)


def parse_osc_wrapper(osc_data, message_index=0):
    # Convert the bytes object to a ctypes array of c_byte
    buffer_array = (c_byte * len(osc_data))(*osc_data)

    # Create the OscMessageMeta structure to hold the result
    message = OscMessageMeta()

    # Create a variable to store the message index
    message_index = c_int(message_index)

    # Call the parse_osc function
    success = fti_osc_lib.parse_osc(buffer_array, len(osc_data), byref(message_index), byref(message))

    if success:
        # Access the parsed values from the message structure
        address = message.Address.decode("utf-8")

        if message.Value:
            # Check how many values were parsed
            value_count = message.ValueLength

            if value_count == 0:
                return address, None, message_index.value, False

            # For each value, access the value and type
            for i in range(value_count):
                # Get the OscValue structure at the current index
                osc_value = ctypes.cast(message.Value + (i * ctypes.sizeof(OscValue)),
                                        ctypes.POINTER(OscValue)).contents

                if osc_value.Type.value == 1:
                    return address, osc_value.IntValue, message_index.value, success
                elif osc_value.Type.value == 2:
                    return address, osc_value.FloatValue, message_index.value, success
                elif osc_value.Type.value == 3:
                    return address, osc_value.BoolValue, message_index.value, success
                elif osc_value.Type.value == 4:
                    return address, osc_value.StringValue.decode("utf-8"), message_index.value, success
    else:
        return None, None, None, success


def create_osc_bool(address, bool_value):
    # Create the OscMessageMeta structure to hold the result
    message = OscMessageMeta()
    message.Address = address.encode('utf-8')
    message.ValueLength = 1
    value = OscValue()
    value.Type = OscValueType(3)
    value.BoolValue = bool_value
    message.Value = ctypes.cast(ctypes.pointer(value), ctypes.c_void_p)

    buf = (c_byte * 4096)()
    buf_len = create_osc_message(buf, message)
    return bytes(buf[:buf_len])
