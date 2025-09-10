## INDUSTRY LEVEL CUSTOM EXCEPTION THAT CAN HANDLE ANY KIND OF ERROR AND PINPOINT THE LOCATION

import sys
import traceback
from typing import Optional, cast

class DocumentPortalException(Exception):
    def __init__(self, error_message, error_details: Optional[object] = None):
        # Normalize message
        if isinstance(error_message, BaseException):
            norm_msg= str(error_message) #f"{error_message.__class__.__name__}: {error_message}"
        else:
            norm_msg = str(error_message)

        # Resolve exc_info (supports: sys module, Exception object, or current context)

        exc_type= exc_value = exc_tb = None
# -- -------------Core start------------------#
        if error_details is None:
            exc_type, exc_value, exc_tb = sys.exc_info()
        else:
            if hasattr(error_details, "exc_info"):
                exc_info_obj= cast(sys, error_details)
                exc_type, exc_value, exc_tb = exc_info_obj.exc_info()

            elif isinstance(error_details, BaseException):
                exc_type, exc_value, exc_tb = type(error_details), error_details, error_details.__traceback__
            else:
                exc_type, exc_value, exc_tb = sys.exc_info()
# - ----------------Core end-----------------------------

        ## Walk to the last frame to report the most relevant location

        last_tb= exc_tb
        while last_tb and last_tb.tb_next:
            last_tb = last_tb.tb_next

        self.file_name= last_tb.tb_frame.f_code.co_filename if last_tb else '<unknown>'
        self.lineno= last_tb.tb_lineno if last_tb else -1
        self.error_message= norm_msg

        # Full pretty traceback (if available)

        if exc_type and exc_tb:
            self.traceback_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        else:
            self.traceback_str = ""

        super().__init__(self.__str__())

    def __str__(self):
        # Compact logger friendly message (no leading spaces)
        base= f"Error in [{self.file_name}] at line[{self.lineno}] | Message: {self.error_message}"
        if self.traceback_str:
            return f"{base}\n{self.traceback_str}"
        return base

    def __repr__(self):
        return f"DocumentPortalException(file= {self.file_name}), lineno= {self.lineno}, message= {self.error_message}"


# CLASS FOR STOCKANLYSER - Tavily API Error
class TavilyAPIError(DocumentPortalException):
    """Exception raised for Tavily API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None,error_details: Optional[object] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message, error_details)

class PortfolioAnalyzerError(DocumentPortalException):
    def __init__(self, message: str, error_details: Optional[object] = None):
        self.message = message
        self.status_code = error_details
        super().__init__(self.message, error_details)

class WhatsAppMessengerError(DocumentPortalException):
    pass

class FileProcessingError(DocumentPortalException):
    """Raised when file processing fails"""
    pass

class EmbeddingError(DocumentPortalException):
    """Raised when embedding generation fails"""
    pass

class ChatError(DocumentPortalException):
    """Raised when chat processing fails"""
    pass

class VectorStoreError(DocumentPortalException):
    """Raised when vector store operations fail"""
    pass





if __name__ == "__main__":
    # demo1 Division error
    # demo 2 str to int error
    try:
        a= int("Str")
    except Exception as e:
        raise TavilyAPIError("Tavily API Error - Please verify Tavily API Key", e) from e

