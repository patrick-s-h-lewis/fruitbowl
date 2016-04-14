/*
Copyright 2008-2010 Gephi
Authors : Mathieu Bastian <mathieu.bastian@gephi.org> Patrick Lewis
Website : http://www.gephi.org

This file is part of Gephi.

Gephi is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

Gephi is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with Gephi.  If not, see <http://www.gnu.org/licenses/>.

Heavily Modified by Patrick Lewis
 */
package org.gephi.toolkit.demos;

public class Main {
 /**
 * This class performs Partitioning on inputted graphs
 * <p>
 * @author Patrick Lewis
 */

    public static void main(String[] args) {
        System.out.println(args[0]);
        System.out.println(args[1]);
        PartitionGraph partitionGraph = new PartitionGraph(args[0],args[1]);
        partitionGraph.script();

    }
}
