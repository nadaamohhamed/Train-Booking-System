#install pyodbc with "pip install pyodbc"
import pyodbc
import models
class database:
    def __init__(self):
        self.connection = pyodbc.connect('DRIVER={SQL Server};Server={TrainBooking.mssql.somee.com};Database=TrainBooking; UID=TrainBookingSys; PWD=123456789',autocommit=True)
        # self.connection = pyodbc.connect('DRIVER={SQL Server};Server={mssql-127165-0.cloudclusters.net,16286};Database=TrainBooking; UID=sakkary; PWD=Kareem20210301',autocommit=True)
        
    def addRecord(self,data):
        cursor = self.connection.cursor()
        sql = f""""""
        if(data.table =="Trip" and len(data.seats) > 0):
            sql = f"""
                INSERT INTO Seat(seat_id,trip_id,status) VALUES         
                """
            i = 0
            for seat in data.seats:
                if(i!= 0):
                    sql+=','
                sql += seat.add()
                i+=1
                if(i == 999):
                    sql +=';'
                    cursor.execute(sql)
                    sql = f"""
                    INSERT INTO Seat(seat_id,trip_id,status) VALUES         
                    """
                    i=0
            if(i > 0):
                cursor.execute(sql)
            
        else:
            cursor = self.connection.cursor()
            sql = f"""
            INSERT INTO {data.add()}
            """
            cursor.execute(sql)
            if(data.table == "Trip"):
                trip = self.getLastRecord("Trip","Trip_id")
                trip.setTrain()
                self.addRecord(trip)
            if(data.table == "Booking"):
                cursor = self.connection.cursor()
                sql = f"""
                    UPDATE TOP({data.no_of_seats}) Seat SET status = 'booked' WHERE trip_id = {data.trip.trip_id} AND status = 'available';
                """
                cursor.execute(sql)
                data.trip = self.selectAll("Trip",f"Trip.trip_id = '{data.trip.trip_id}'")

    def getLastRecord(self,table_name,column):
        cursor = self.connection.cursor()
        sql =f"""
        SELECT MAX({column})
        FROM {table_name};
        """
        cursor.execute(sql)
        id = cursor.fetchone()[0]
        cursor = self.connection.cursor()
        sql =f"""
        SELECT *
        FROM {table_name} WHERE {column} = {id};
        """
        cursor.execute(sql)
        trip=None
        row = cursor.fetchall()[0]
        if(table_name == "Trip"):
            trip = models.Trip(row)
            trip.train= self.selectAll("Train",f"train_id = '{row[1]}'")[0]
        return trip

    def deleteRecord(self,data):
        cursor = self.connection.cursor()
        sql = f"""
        DELETE FROM {data.table} WHERE {data.key()};
        """
        cursor.execute(sql)
        if(data.table == 'Booking'):
            cursor = self.connection.cursor()
            sql = f"""
                UPDATE TOP({data.no_of_seats}) Seat SET status = 'available' WHERE trip_id = {data.trip.trip_id} AND status = 'booked';
            """
            cursor.execute(sql)

    def selectAll(self,tablename,where=None):
        cursor = self.connection.cursor()
        sql = ""
        if(tablename == 'Trip'):
            sql = """select Trip.*,count(Seat.seat_id), Train.*
            from Trip,Train,Seat where Trip.train_id = Train.train_id AND Seat.trip_id = Trip.trip_id"""
            if(where):
                sql += f" AND {where}"
            sql += """ GROUP BY Trip.Trip_id,Trip.train_id,Trip.price,Trip.start_date,Trip.end_date,Trip.departure_station,Trip.arrival_station,
                        Train.train_id,Train.capacity,Train.status,Train.no_of_carts,Train.manufacturer"""
        elif(tablename == 'Booking'):
            sql = """SELECT Booking.*,Account.*,Trip.*,Train.* FROM Booking,Account,Trip,Train
            WHERE Account.account_id = Booking.account_id AND Trip.trip_id = Booking.trip_id AND Trip.train_id = Train.train_id
            """
            if(where):
                sql += f" AND {where}"
        elif(where == None):
            sql = f"""select * from {tablename}"""
        else:
            sql = f"""select * from {tablename} WHERE {where}"""
        cursor.execute(sql)
        rows = cursor.fetchall()
        li = []
        for row in rows: 
            if(tablename == "Account"):
                if(row[3] == "Customer"):
                    li.append(models.Customer(row))
                else :
                    li.append(models.Admin(row))
            elif(tablename == "Train"):
                li.append(models.Train(row))
            elif(tablename=="Trip"):
                trip = models.Trip(row)
                trip.train = models.Train(row[8::])
                # trip.train = self.selectAll("Train",f"train_id = '{row[1]}'")[0]
                # trip.seats = self.selectAll("Seat",f"trip_id = '{row[0]}'")
                trip.ETA = trip.end_date-trip.start_date
                li.append(trip)
            elif(tablename=="Seat"):
                li.append(models.Seat(row))
            elif(tablename=="Booking"):
                booking = models.Booking(row)
                booking.account = models.Account(row[4::])
                train = models.Train(row[19::])
                booking.trip = models.Trip(row[12::])
                booking.trip.train = train
                # booking.trip = self.selectAll("Trip",f"trip_id = {row[2]};")[0]
                # booking.account = self.selectAll("Account",f"account_id = {row[1]};")[0]
                booking.set_seats_num(booking.no_of_seats)
                li.append(booking)
        return li
    
    def count(self,tablename,where=None):
        return len(self.selectAll(tablename,where))
    
    def update(self,data):
        cursor = self.connection.cursor()
        if(data.table == 'Booking'):
            old_booking = self.selectAll('Booking',data.key())[0]
            deff = data.no_of_seats-old_booking.no_of_seats
            if(deff!=0):
                cursor = self.connection.cursor()
                sql=""""""
                if(deff < 0):
                    sql = f"""
                    UPDATE TOP({abs(deff)}) Seat SET status = 'available' WHERE trip_id = {data.trip.trip_id} AND status = 'booked';
                    """
                elif(deff > 0):
                    sql = f"""
                    UPDATE TOP({abs(deff)}) Seat SET status = 'booked' WHERE trip_id = {data.trip.trip_id} AND status = 'available';
                    """
                cursor.execute(sql)
        sql = f"""
            UPDATE {data.table} SET {data.update()};
        """
        cursor.execute(sql)

    def getTrips(self,seats,arrival_station=None,departure_station=None,start_date=None,end_date=None):
        cursor = self.connection.cursor()
        sql = f"""SELECT Trip.* , COUNT(Seat.seat_id) , Train.*
                FROM Trip,Seat,Train
                Where
                Trip.trip_id = Seat.trip_id
                AND Trip.train_id = Train.train_id
                AND Seat.status = 'available'
                """
        if(arrival_station):
            sql += f"AND Trip.arrival_station = '{arrival_station}' "
        if(departure_station):
            sql += f"AND Trip.departure_station = '{departure_station}' "
        if(start_date):
            sql += f"AND Trip.start_date = '{start_date}' "
        if(end_date):
            sql += f"AND Trip.end_date = '{end_date}' "
        sql += f"""GROUP BY Trip.trip_id ,Trip.train_id,Trip.price,Trip.start_date,Trip.end_date,Trip.departure_station,Trip.arrival_station
                ,Train.train_id,Train.capacity,Train.status,Train.no_of_carts,Train.manufacturer
                HAVING COUNT(Seat_id) >= {seats};"""
        li =[]
        cursor.execute(sql)
        rows = cursor.fetchall()
        for row in rows:
            trip = models.Trip(row)
            trip.train = models.Train(row[8::])
            # trip.train = self.selectAll("Train",f"train_id = '{row[1]}'")[0]
            # trip.seats = self.selectAll("Seat",f"trip_id = '{row[0]}' AND status = 'available'")
            trip.ETA = trip.end_date-trip.start_date
            li.append(trip)
        return li

    def reportTrips(self):
        cursor = self.connection.cursor()
        sql = """SELECT departure_station , arrival_station , COUNT(Trip.trip_id) , count(Booking.trip_id) , AVG(Trip.price) 
                FROM Trip full OUTER JOIN Booking on Trip.trip_id = Booking.trip_id GROUP BY departure_station ,arrival_station;"""
        cursor.execute(sql)
        return cursor.fetchall()
    
    def tableSizes(self):
        cursor = self.connection.cursor()
        sql = """SELECT COUNT(*) from Account """
        sql += """UNION ALL SELECT COUNT(*) from Booking """
        sql += """UNION ALL SELECT COUNT(*) from Train """
        sql += """UNION ALL SELECT COUNT(*) from Trip ;"""
        cursor.execute(sql)
        return cursor.fetchall()