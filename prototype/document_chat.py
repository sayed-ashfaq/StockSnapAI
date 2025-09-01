import streamlit as st
import os
import tempfile
from datetime import datetime
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_openai import OpenAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain import hub
from langchain_core.messages import HumanMessage, AIMessage
import pandas as pd

load_dotenv()


class DocumentChat:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.llm = init_chat_model(model='gemini-2.0-flash', model_provider="google_genai")

        # Initialize session state
        if 'vector_store' not in st.session_state:
            st.session_state.vector_store = None
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'current_document' not in st.session_state:
            st.session_state.current_document = None
        if 'document_summary' not in st.session_state:
            st.session_state.document_summary = None

    def load_document(self, uploaded_file):
        """Load and process uploaded document"""
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name

            # Load document based on file type
            if uploaded_file.name.lower().endswith('.pdf'):
                loader = PyPDFLoader(tmp_file_path)
            # elif uploaded_file.name.lower().endswith('.txt'):
            #     loader = TextFileLoader(tmp_file_path)
            else:
                st.error("Unsupported file type. Please upload PDF or TXT files.")
                os.unlink(tmp_file_path)
                return False

            # Load and split documents
            docs = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            splits = text_splitter.split_documents(docs)

            # Create vector store
            vector_store = InMemoryVectorStore(embedding=self.embeddings)
            vector_store.add_documents(documents=splits)

            # Store in session state
            st.session_state.vector_store = vector_store
            st.session_state.current_document = uploaded_file.name
            st.session_state.chat_history = []  # Reset chat history

            # Generate document summary
            self.generate_document_summary(docs)

            # Clean up temp file
            os.unlink(tmp_file_path)

            return True

        except Exception as e:
            st.error(f"Error loading document: {str(e)}")
            if 'tmp_file_path' in locals():
                os.unlink(tmp_file_path)
            return False

    def generate_document_summary(self, docs):
        """Generate a summary of the uploaded document"""
        try:
            # Get first few pages/chunks for summary
            content = "\n\n".join([doc.page_content for doc in docs[:3]])  # First 3 chunks

            summary_prompt = f"""
             Please provide a comprehensive summary of this financial document. Include:

             1. **Document Type & Overview**: What type of document is this? (earnings report, annual report, audit report, etc.)
             2. **Key Financial Highlights**: Important financial metrics, performance indicators
             3. **Red Flags & Concerns**: Any potential risks, warnings, or concerning trends
             4. **Management Discussion**: Key points from management commentary
             5. **Future Outlook**: Forward-looking statements or guidance

             Document Content:
             {content[:3000]}...

             Please structure your response clearly with the above sections.
             """

            response = self.llm.invoke([HumanMessage(content=summary_prompt)])
            st.session_state.document_summary = response.content

        except Exception as e:
            st.error(f"Error generating summary: {str(e)}")

    def chat_with_document(self, question):
        """Chat with the uploaded document"""
        if not st.session_state.vector_store:
            return "Please upload a document first."

        try:
            # Retrieve relevant documents
            retrieved_docs = st.session_state.vector_store.similarity_search(question, k=4)
            docs_content = "\n\n".join([f"[Chunk {i + 1}]: {doc.page_content}" for i, doc in enumerate(retrieved_docs)])

            # Get RAG prompt from hub
            try:
                prompt = hub.pull("rlm/rag-prompt")
                formatted_prompt = prompt.invoke({"question": question, "context": docs_content})
            except:
                # Fallback prompt if hub is not available
                formatted_prompt = f"""
                 You are an AI assistant helping analyze financial documents. Use the following context to answer the user's question.

                 Context:
                 {docs_content}

                 Question: {question}

                 Instructions:
                 - Answer based on the provided context
                 - If you cannot find relevant information, say so
                 - Provide specific citations when possible
                 - Focus on factual information from the document
                 - Highlight any red flags or important insights

                 Answer:
                 """

            # Generate response
            response = self.llm.invoke([HumanMessage(content=str(formatted_prompt))])

            # Add citations
            answer_with_citations = f"{response.content}\n\n**Sources:** Based on {len(retrieved_docs)} relevant sections from the document."

            return answer_with_citations

        except Exception as e:
            return f"Error processing question: {str(e)}"

    def render(self):
        st.header("📄 Document Chat & Analysis")
        st.markdown(
            "Upload financial documents (PDF, TXT) and chat with them using AI. Get summaries, ask questions, and detect red flags.")

        # File upload section
        with st.container():
            st.subheader("📁 Upload Document")

            uploaded_file = st.file_uploader(
                "Choose a financial document",
                type=['pdf', 'txt'],
                help="Upload earnings reports, annual reports, audit reports, or earnings call transcripts"
            )

            if uploaded_file is not None:
                if st.session_state.current_document != uploaded_file.name:
                    with st.spinner("Processing document..."):
                        if self.load_document(uploaded_file):
                            st.success(f"✅ Document '{uploaded_file.name}' loaded successfully!")
                        else:
                            st.error("❌ Failed to load document")
                else:
                    st.info(f"📄 Current document: **{st.session_state.current_document}**")

        # Document summary section
        if st.session_state.current_document and st.session_state.document_summary:
            st.subheader("📋 Document Summary")
            with st.expander("View Document Summary", expanded=True):
                st.markdown(st.session_state.document_summary)

        # Chat interface
        if st.session_state.current_document:
            st.subheader("💬 Chat with Document")

            # Display chat history
            if st.session_state.chat_history:
                st.markdown("**Chat History:**")
                for i, (question, answer) in enumerate(st.session_state.chat_history):
                    with st.container():
                        # User question
                        st.markdown(f"**You:** {question}")
                        # AI response
                        st.markdown(f"**AI:** {answer}")
                        st.divider()

            # Question input
            with st.form("chat_form", clear_on_submit=True):
                question = st.text_area(
                    "Ask a question about the document:",
                    placeholder="e.g., What are the key financial highlights? Are there any red flags? What's the revenue growth?",
                    height=100
                )

                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    ask_button = st.form_submit_button("🔍 Ask Question", use_container_width=True)
                with col2:
                    clear_button = st.form_submit_button("🗑️ Clear Chat", use_container_width=True)

            # Quick questions
            st.markdown("**Quick Questions:**")
            quick_questions = [
                "What are the key financial highlights?",
                "Are there any red flags or concerns?",
                "What is the revenue and profit trend?",
                "What risks are mentioned in the document?",
                "What is management's outlook for the future?",
                "What are the main business segments?"
            ]

            cols = st.columns(2)
            for i, q in enumerate(quick_questions):
                with cols[i % 2]:
                    if st.button(q, key=f"quick_{i}", use_container_width=True):
                        question = q
                        ask_button = True

            # Handle form submission
            if ask_button and question.strip():
                with st.spinner("Analyzing document..."):
                    answer = self.chat_with_document(question)

                    # Add to chat history
                    st.session_state.chat_history.append((question, answer))

                    # Display new response
                    st.markdown("**Latest Response:**")
                    st.markdown(f"**You:** {question}")
                    st.markdown(f"**AI:** {answer}")

                    # Rerun to update chat history display
                    st.rerun()

            if clear_button:
                st.session_state.chat_history = []
                st.rerun()

        else:
            st.info("👆 Upload a document to start chatting with it!")

            # Example document types
            st.markdown("**Supported document types:**")
            doc_types = {
                "📊 Earnings Reports": "Quarterly/Annual earnings releases",
                "📈 Annual Reports": "10-K, annual company reports",
                "🔍 Audit Reports": "Independent auditor reports",
                "🎙️ Earnings Transcripts": "Earnings call transcripts",
                "📋 Financial Statements": "Balance sheets, income statements"
            }

            for doc_type, description in doc_types.items():
                st.write(f"{doc_type}: {description}")

        # Export chat history
        if st.session_state.chat_history:
            st.subheader("📤 Export Chat")

            # Prepare export data
            export_data = {
                "Document": st.session_state.current_document,
                "Export Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Chat History": []
            }

            for q, a in st.session_state.chat_history:
                export_data["Chat History"].append({
                    "Question": q,
                    "Answer": a
                })

            # Convert to text format for download
            export_text = f"Document Analysis Chat Export\n"
            export_text += f"Document: {st.session_state.current_document}\n"
            export_text += f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            export_text += f"{'=' * 50}\n\n"

            for i, (q, a) in enumerate(st.session_state.chat_history, 1):
                export_text += f"Q{i}: {q}\n"
                export_text += f"A{i}: {a}\n"
                export_text += f"{'-' * 30}\n\n"

            st.download_button(
                label="📥 Download Chat History",
                data=export_text,
                file_name=f"chat_history_{st.session_state.current_document}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )

        # Footer
        st.markdown("---")
        st.markdown(
            "*💡 Tip: Ask specific questions about financial metrics, risks, and key insights. The AI will provide citations from the document.*")