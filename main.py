#importing dependencies and spackages
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import sys

DB_NAME = "personal_finance5.db"

def create_connection():
    try:
        conn = sqlite3.connect(DB_NAME)
        print("Connected to the database successfully")
        return conn
    except Exception as e:
        print(str(e))

# creating necessary tables
def create_table(conn):
    c=conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS income
                 (month text, salary real)''')
    c.execute('''CREATE TABLE IF NOT EXISTS saving
                 (month text, amount_saved real,comments text)''')
    c.execute('''CREATE TABLE IF NOT EXISTS budget
                 (month text, category text, budget_amount real)''')
    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (month text, category text, amount_spent real,comments text)''')
    print("Successfully created the tables")

#function to entry in tables
def add_income(conn,salary):
    c= conn.cursor()
    c.execute("INSERT INTO income values (?,?)",(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), salary))
    conn.commit()
    print('Salary has been successfully added')

def create_budget(conn,category_budgets):
    c = conn.cursor()
    for category, amount in category_budgets.items():
        c.execute("INSERT INTO budget VALUES (?, ?, ?)", (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), category, amount))
    conn.commit()
    print('Budget has been planned and added to budget table')
    
def add_expense(conn, category, amount_spent,comments):
    c = conn.cursor()
        
    c.execute("INSERT INTO expenses VALUES (?, ?, ?, ?)",
              (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), category, amount_spent, comments))
    conn.commit()
    print(f"Expenses {category} {amount_spent} has been successfully added")

def add_saving(conn,amount_saved,comments):
    c = conn.cursor()
    c.execute("INSERT INTO saving VALUES (?, ?, ?)",
              (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  amount_saved, comments))
    conn.commit()
    print(f"Saving amount {amount_saved} successfully added")

#function to generate reports
def generate_report_and_analyze_savings(conn, month):
    c = conn.cursor()
    df_budget = pd.read_sql_query(f"SELECT strftime('%Y-%m',month) as month,category,budget_amount FROM budget WHERE strftime('%Y-%m',month) = '{month}'", conn)
    query = """
        SELECT strftime('%Y-%m',month) as month, category, SUM(amount_spent) AS amount_spent 
        FROM expenses 
        WHERE strftime('%Y-%m',month) = ? 
        GROUP BY category
    """
    df_expenses = pd.read_sql_query(query, conn, params=(month,))
    
    

    # merging budget and expenses for comparison
    df_merged = pd.merge(df_budget,df_expenses, on =['month', 'category'],how='left')

    #calculate difference
    df_merged['difference'] = df_merged['budget_amount'] - df_merged['amount_spent']
    print(df_merged)

    #visualizing the budget vs acutal expenses
    df_merged.plot(x='category',y =['budget_amount','amount_spent'],kind= 'bar')
    plt.savefig('expenses_plot.png')  
    plt.show()
    
    
        


    # analyzing the saving
    income = c.execute(f"SELECT salary FROM income WHERE strftime('%Y-%m',month) = '{month}'").fetchone()
    income_amount = income[0] if income else 0
    
    
    # Get expenses summary
    expenses_query = """
    SELECT category, SUM(amount_spent) as total_spent
    FROM expenses
    WHERE strftime('%Y-%m',month) = ?
    GROUP BY category
    """
    expenses_df = pd.read_sql_query(expenses_query, conn, params=(month,))
    # Calculate total expenses
    total_expenses = expenses_df['total_spent'].sum()

    
    
    savings = income_amount - total_expenses


    if savings > 0:
        advice = f"You saved {savings}. Good job! Consider investing or saving more."
        
    else:
        advice = f"You overspent by {-savings}. Try reducing expenses in the next month."
        
    add_saving(conn,savings,advice)
    print(advice)

    user_input = input("Do you want to save financial_summary_to_csv press y for yes and n for no: ")
    if user_input == 'y':
        

        # Get budget planning
        budget_query = "SELECT category, budget_amount FROM budget WHERE strftime('%Y-%m',month) = ?"
        budget_df = pd.read_sql_query(budget_query, conn, params=(month,))
        
    
        #creating summary data frame
        saving_df = pd.DataFrame({
            'Income' :[income_amount],
            'Total Expenses' : [total_expenses],
            'Savings' : [savings]
        })
        # Merge income, expenses, and budget into a single DataFrame
        financial_summary_df = pd.concat([saving_df, budget_df.rename(columns={'budget_amount': 'Budget Amount'})], axis=1)
        expenses_df.rename(columns={'total_spent': 'Amount Spent'}, inplace=True)
    
        # Final merge with expenses
        final_summary_df = financial_summary_df.join(expenses_df.set_index('category'), on='category')
    
    
        # Save to CSV
        final_summary_df.to_csv('financial_summary.csv', index=False)
        print("Saved")





def delete_row(conn,tablename,row_id):
    c = conn.cursor()
    c.execute(f"DELETE FROM {tablename} where id = ?;",(row_id,))
    conn.commit()
    print(f"{row_id} from {tablename} was deleted successfully")

def display_table(conn,tablename):
    df = pd.read_sql_query(f"select * FROM {tablename}",conn)
    print(df)

INPUT_STRING="""
Enter the option:
    1. CREATE table
    2. ADD Salary
    3. ADD budget_planning
    4. ADD expenses
    5. Display tables
    6. Delete row from tables
    7. Generate Reports and analyze savings
 Press 0 key to EXIT
"""
def main():
    while True:
        user_input = input(INPUT_STRING)
        conn = create_connection()
    
        if user_input == "1":
            create_table(conn)
    
        elif user_input == "2":
            salary = int(input("Enter salary for this month:"))
            add_income(conn,salary)

        elif user_input == "3":
            category_budgets = {}
            while True:
                if input("Enter 1 for entry budget_planning or 0 to stop") == '0':
                    break
                category = input("Enter category: ")
                budget_amount = int(input(f"Enter budget_amount {category}:"))
                category_budgets[category] = budget_amount
            create_budget(conn,category_budgets)
            
    
        elif user_input == "4":
            while True:
                if input("Enter 1 to entry expenses or 0 to stop") == '0':
                    break
                category = input("Enter category: ")
                amount_spent = input(f"Enter budget_amount {category}: ")
                comments = input("Enter comments")
                add_expense(conn,category,amount_spent,comments)
                
        elif user_input == "5":
            try:
                table_name = input("Enter the tablename you want to display: ")
                display_table(conn,table_name)
            except Exception as e:
                print(str(e))
                              

        elif user_input == '6':
            table_name = input("Enter the tablename which row you want to delete: ")
            row_id = input("Enter the row_id you want to delete:")
            delete_row(conn,table_name,row_id)

        elif user_input == '7':
            month = input("Enter the year and month in yyyy-mm format: ")
            generate_report_and_analyze_savings(conn,month)

        elif user_input == '8':
            filename = input("Enter the filename you want it to be saved as: ")
            month = input("Enter the year and month in yyyy-mm format: ")
            save_financial_summary_to_csv(conn, month, filename)
            
            
            
        elif user_input == '0':
            break
            
        else:
            exit

if __name__ == "__main__":
    main()