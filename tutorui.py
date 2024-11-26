    # Create a search bar
    search_query = st.text_input("Search student data by student name, grade, or ID", "").strip().lower()

    # Apply search filters and grade logic
    filtered_data = [
        entry for entry in table_data
        if (
            # Check if the query is a grade ("a", "b", "c", "d") and matches the grade
            (len(search_query) == 1 and search_query in ["a", "b", "c", "d"] 
             and entry['Grade'].lower() == search_query)
            or
            # Otherwise, treat the query as a student name or ID
            (
                len(search_query) > 1
                or search_query not in ["a", "b", "c", "d"]
            )
            and (
                search_query in entry['Student'].lower() 
                or search_query in str(entry['ID']).lower()
            )
        )
        # Exclude entries with "Grade not found, please review manually"
        and entry['Grade'].lower() != "grade not found, please review manually"
    ]

    # data for display
    if search_query:
        display_df = pd.DataFrame(filtered_data)
    else:
        display_df = df if not show_top_5 else df.head(5)

    # display unified table
    st.write("### Student Data (for best viewing, download and top left align):")
    st.dataframe(display_df[['ID', 'Student', 'Timestamp', 'Grade', 'Questions', 'Feedback']], width=1000, height=400)

    # add conversation finder
    st.write("### Conversation Finder:")
    conversation_search_id = st.text_input("Search conversation logs by ID", "").strip()

    # check if the ID exists in conversation data to pull up conversation log
    if conversation_search_id:
        matching_logs = [
            entry for entry in conversation_data if str(entry['id']) == conversation_search_id
        ]

        if matching_logs:
            log = matching_logs[0]
            st.write(f"### Conversation Log for ID {log['id']} - {log['username']} ({log['timestamp']}):")
            for message in log["messages"]:
                role = message["role"].capitalize()
                content = message["content"]
                st.write(f"**{role}:** {content}")
        else:
            st.write("No conversation log found for the given ID.")
